from collections import Counter
from dataclasses import dataclass
import re

from lxml import etree

from app.core.config import Config

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


@dataclass(frozen=True)
class Span:
    key: str
    start: int
    end: int
    title: str


def paragraph_text(node: etree._Element) -> str:
    return "".join(node.itertext()) if node.tag != f"{{{W}}}p" else "".join(node.xpath(".//w:t/text()", namespaces=NS)).strip()


def normalize(match: re.Match, width: int, entity_kind: str = "span") -> str:
    groups = match.groupdict()
    if groups.get("start") is not None and groups.get("end") is not None:
        return f"T{int(groups['start']):0{width}d}-T{int(groups['end']):0{width}d}"
    value = groups.get("id")
    if value is None or not value.isdecimal():
        raise ValueError("Span ID groups must contain decimal numbers")
    return f"{'Tower' if entity_kind == 'tower' else 'Span'}_{int(value):0{width}d}"


def detect(body: etree._Element, config: Config) -> tuple[list[Span], list[str]]:
    patterns = [re.compile(p, re.I) for p in config.span_patterns]
    closing = [re.compile(p, re.I) for p in config.closing_patterns]
    starts: list[tuple[str, int, str]] = []
    end = len(body)
    active = config.start_after is None
    marker = re.compile(config.start_after, re.I) if config.start_after else None
    for index, node in enumerate(body):
        if node.tag == f"{{{W}}}p":
            style = node.find("w:pPr/w:pStyle", NS)
            style_id = style.get(f"{{{W}}}val", "") if style is not None else ""
            if style_id.lower().startswith("toc") or node.find(".//w:instrText", NS) is not None:
                continue
            text = paragraph_text(node)
            if not active:
                if marker.fullmatch(text):
                    active = True
                continue
            if starts and any(p.fullmatch(text) for p in closing):
                end = index
                break
            if config.table_column is not None:
                continue
            if config.heading_only and style_id not in config.heading_styles:
                continue
        elif active and node.tag == f"{{{W}}}tbl" and config.table_column is not None:
            # The profile identifies detail tables, whose first row is a header
            # and second row holds the record. Keep the entire table and images.
            rows = node.findall("w:tr", NS)
            if len(rows) < 2:
                continue
            cells = rows[1].findall("w:tc", NS)
            if len(cells) <= config.table_column:
                continue
            text = "".join(cells[config.table_column].xpath(".//w:t/text()", namespaces=NS)).strip()
        else:
            continue
        for pattern in patterns:
            match = pattern.fullmatch(text)
            if match:
                key = normalize(match, config.number_width, config.entity_kind)
                if not (config.merge_consecutive and starts and starts[-1][0] == key):
                    starts.append((key, index, text))
                break
    spans = [Span(key, start, starts[i + 1][1] if i + 1 < len(starts) else end, title)
             for i, (key, start, title) in enumerate(starts)]
    duplicates = sorted(key for key, count in Counter(s.key for s in spans).items() if count > 1)
    return spans, duplicates
