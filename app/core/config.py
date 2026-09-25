"""Validated parser configuration; patterns are intentionally user-editable."""
from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
import string

import yaml

DEFAULT_PATTERNS = [
    r"(?:Span\s+)?(?:Tower\s*|T\.?\s*)?(?P<start>\d+)\s*[-–—]\s*(?:Tower\s*|T\.?\s*)?(?P<end>\d+)",
    r"Span\s*(?:No\.?\s*)?(?P<id>\d+)",
]


@dataclass
class Config:
    span_patterns: list[str] = field(default_factory=lambda: DEFAULT_PATTERNS.copy())
    profile: str = "generic"
    entity_kind: str = "span"
    start_after: str | None = None
    table_column: int | None = None
    merge_consecutive: bool = False
    heading_only: bool = False
    heading_styles: list[str] = field(default_factory=lambda: ["Heading1", "Heading2", "Heading3"])
    closing_patterns: list[str] = field(default_factory=list)
    include_preamble: bool = False
    personalize_preamble: bool = False
    number_width: int = 3
    output_template: str = "{span_id}.docx"

    def __post_init__(self) -> None:
        if self.entity_kind not in {"span", "tower"}:
            raise ValueError("entity_kind must be span or tower")
        if self.start_after is not None:
            re.compile(self.start_after, re.I)
        if self.table_column is not None and (type(self.table_column) is not int or self.table_column < 0):
            raise ValueError("table_column must be a nonnegative integer")
        if type(self.merge_consecutive) is not bool:
            raise ValueError("merge_consecutive must be a boolean")
        if type(self.personalize_preamble) is not bool or (self.personalize_preamble and not self.include_preamble):
            raise ValueError("personalize_preamble requires include_preamble=true")
        for name in ("span_patterns", "closing_patterns", "heading_styles"):
            value = getattr(self, name)
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                raise ValueError(f"{name} must be a list of strings")
        if not self.span_patterns:
            raise ValueError("At least one span pattern is required")
        for pattern in self.span_patterns:
            compiled = re.compile(pattern, re.IGNORECASE)
            groups = compiled.groupindex
            if not ("id" in groups or {"start", "end"} <= groups.keys()):
                raise ValueError("Span patterns need named group 'id' or 'start' and 'end'")
        for pattern in self.closing_patterns:
            re.compile(pattern, re.IGNORECASE)
        if type(self.number_width) is not int or not 1 <= self.number_width <= 12:
            raise ValueError("number_width must be between 1 and 12")
        if type(self.heading_only) is not bool or type(self.include_preamble) is not bool:
            raise ValueError("heading_only and include_preamble must be booleans")
        fields = [item[1] for item in string.Formatter().parse(self.output_template) if item[1] is not None]
        if not fields or any(item != "span_id" for item in fields):
            raise ValueError("output_template must contain {span_id} and no other fields")
        self.filename("T001-T002")

    def filename(self, span_id: str) -> str:
        name = self.output_template.format(span_id=span_id)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.docx", name) or ".." in name:
            raise ValueError("Output name must be a safe .docx filename without directories")
        return name

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, path: Path | None) -> "Config":
        if path is None:
            return cls()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Configuration must be a YAML mapping")
        unknown = set(data) - cls.__dataclass_fields__.keys()
        if unknown:
            raise ValueError(f"Unknown configuration keys: {sorted(unknown)}")
        return cls(**data)


    @classmethod
    def for_source(cls, source: Path, explicit: Path | None = None) -> "Config":
        if explicit is not None:
            return cls.load(explicit)
        profiles = yaml.safe_load(Path(__file__).with_name("profiles.yaml").read_text(encoding="utf-8"))
        matches = [item for item in profiles if re.search(item["filename"], source.name, re.I)]
        if len(matches) > 1:
            raise ValueError("Ambiguous report type; specify --config")
        return cls(**matches[0]["config"]) if matches else cls()
