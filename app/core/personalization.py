"""Scope existing report introductions and summaries to one detected entity."""
from collections import Counter
import re
from lxml import etree
from app.core.detection import NS, W, Span

SUPPORTED = {'clearance', 'sag', 'phase_spacing', 'sections', 'tower_inclination', 'tower_height'}
RANGE = re.compile(r'\bSPAN\s*:?\s*\d+#?\s*[-–—]\s*\d+#?', re.I)


def text(node):
    return ''.join(t.text or '' for t in node.iter(f'{{{W}}}t'))


def replace_text(node, pattern, replacement):
    """Replace across Word runs without flattening formatting, fields or drawings."""
    texts = list(node.iter(f'{{{W}}}t'))
    original = ''.join(t.text or '' for t in texts)
    for match in reversed(list(pattern.finditer(original))):
        offset = 0
        for t in texts:
            value = t.text or ''
            end = offset + len(value)
            if offset < match.end() and end > match.start():
                left = max(0, match.start() - offset)
                right = min(len(value), match.end() - offset)
                t.text = value[:left] + (replacement if offset <= match.start() < end else '') + value[right:]
                t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            offset = end


def label(span):
    if span.key.startswith('Tower_'):
        return 'MENARA ' + span.key.split('_')[1]
    return 'SPAN ' + span.key


def scope_identity(root, span):
    for paragraph in root.iter(f'{{{W}}}p'):
        replace_text(paragraph, RANGE, label(span))


def key_from_cell(value, tower=False):
    if tower:
        match = re.fullmatch(r'\s*(\d+)\s*', value)
        return (int(match[1]),) if match else None
    # A suffix can contain phase position or LiPowerline's internal pair label.
    match = re.fullmatch(r'\s*(\d+)\s*[-–—]\s*(\d+)(?:\s*Fasa.*|\(\d+_\d+\))?\s*', value, re.I)
    return (int(match[1]), int(match[2])) if match else None


def personalize(root, span: Span, preamble_count: int, profile: str):
    if profile not in SUPPORTED:
        raise ValueError(f'No summary personalization rule for profile {profile}')
    body = root.find('w:body', NS)
    preamble = list(body)[:preamble_count]
    tower = span.key.startswith('Tower_')
    wanted = tuple(int(v) for v in re.findall(r'\d+', span.key))
    detail_counts = Counter()
    summary_counts = Counter()
    recap_tables = []
    summary_rows = 0
    for table in [n for n in preamble if n.tag == f'{{{W}}}tbl']:
        rows = table.findall('w:tr', NS)
        if not rows:
            continue
        headers = [' '.join(text(c).split()).lower() for c in rows[0].findall('w:tc', NS)]
        if headers == ['jenis deteksi', 'kritis', 'bahaya', 'other', 'jumlah']:
            recap_tables.append(table)
            continue
        column = next((i for i, h in enumerate(headers) if h in {'span', 'nomor dan posisi span', 'nomor menara'}), None)
        if column is None:
            continue  # Reference limits and legend tables remain untouched.
        kept = 0
        previous_key = None
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            if len(cells) <= column:
                raise ValueError('Unsupported merged summary row; refusing an incomplete summary')
            key = key_from_cell(text(cells[column]), tower)
            merge = cells[column].find('w:tcPr/w:vMerge', NS)
            if key is None and not text(cells[column]).strip() and merge is not None and merge.get(f'{{{W}}}val', 'continue') == 'continue':
                key = previous_key
            if key is None:
                raise ValueError('Unrecognized summary identity; review report profile')
            previous_key = key
            if key != wanted:
                table.remove(row)
            else:
                kept += 1
                if profile == 'clearance':
                    severity = text(cells[-1]).strip().casefold()
                    summary_counts[severity if severity in {'kritis', 'bahaya'} else 'other'] += 1
        if not kept:
            raise ValueError(f'No summary rows found for {span.key}')
        summary_rows += kept
    for table in list(body)[preamble_count:]:
        if table.tag != f'{{{W}}}tbl':
            continue
        rows = table.findall('w:tr', NS)
        if len(rows) < 2:
            continue
        detail_counts['rows'] += 1
    if summary_rows and summary_rows != detail_counts['rows']:
        raise ValueError('Summary/detail row count mismatch')
    if recap_tables and not summary_rows:
        raise ValueError('Cannot calculate clearance totals without matching summary rows')
    for table in recap_tables:
        values = [summary_counts['kritis'], summary_counts['bahaya'], summary_counts['other'], summary_rows]
        for row in table.findall('w:tr', NS)[1:]:
            cells = row.findall('w:tc', NS)
            if len(cells) != 5:
                raise ValueError('Unexpected clearance totals table')
            for cell, value in zip(cells[1:], values):
                replace_text(cell, re.compile(r'^.*$', re.S), str(value))
    for node in preamble:
        scope_identity(node, span)
    # Some source covers have no range (e.g. Sag); explicitly identify their scope.
    first_title = next((n for n in preamble if n.tag == f'{{{W}}}p' and text(n).strip()), None)
    if first_title is not None and label(span) not in text(first_title):
        runs = first_title.xpath('.//w:t', namespaces=NS)
        if runs:
            runs[-1].text = (runs[-1].text or '').rstrip() + ' — ' + label(span)
