"""Read and write OPC packages without loading media into memory."""
from copy import deepcopy
from pathlib import Path
import os
import posixpath
import shutil
import tempfile
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree

from app.core.detection import NS, W, Span

R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
DOC = "word/document.xml"
# These relationships must be explicitly referenced in the retained XML.
EXPLICIT = {"image", "header", "footer", "hyperlink", "chart", "oleObject", "package", "aFChunk", "control", "diagramData", "diagramLayout", "diagramQuickStyle", "diagramColors"}


def parse(data: bytes) -> etree._Element:
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    node = etree.fromstring(data, parser)
    if node.getroottree().docinfo.doctype:
        raise ValueError("XML DTDs are not supported")
    return node


def xml(node: etree._Element) -> bytes:
    return etree.tostring(node, xml_declaration=True, encoding="UTF-8", standalone=True)


def relpath(part: str) -> str:
    folder, name = posixpath.split(part)
    return posixpath.join(folder, "_rels", name + ".rels") if part else "_rels/.rels"


def resolve(part: str, target: str) -> str:
    target = unquote(urlsplit(target).path)
    result = posixpath.normpath(posixpath.join(posixpath.dirname(part), target)) if not target.startswith("/") else target[1:]
    if result.startswith("../") or "\\" in result or result in {"", ".", ".."}:
        raise ValueError(f"Unsafe relationship target: {target}")
    return result


class Package:
    def __init__(self, path: Path):
        self.path = path
        self.archive = ZipFile(path)
        try:
            names = self.archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Package contains duplicate ZIP entries")
            self.names = set(names)
            self.root = parse(self.archive.read(DOC))
            self.body = self.root.find("w:body", NS)
            if self.body is None:
                raise ValueError("Expected a transitional WordprocessingML document body")
            self.types = parse(self.archive.read("[Content_Types].xml"))
            self.relationships: dict[str, etree._Element] = {}
        except Exception:
            self.archive.close()
            raise

    def __enter__(self) -> "Package":
        return self

    def __exit__(self, *_args) -> None:
        self.archive.close()

    def section_properties(self) -> list[tuple[int, etree._Element]]:
        sections = []
        inherited: dict[tuple[str, str], etree._Element] = {}
        for i, node in enumerate(self.body):
            section = node if node.tag == f"{{{W}}}sectPr" else node.find("w:pPr/w:sectPr", NS)
            if section is None:
                continue
            copy = deepcopy(section)
            for kind in ("headerReference", "footerReference"):
                for ref in copy.findall(f"w:{kind}", NS):
                    inherited[(kind, ref.get(f"{{{W}}}type", "default"))] = deepcopy(ref)
            current = {(etree.QName(ref).localname, ref.get(f"{{{W}}}type", "default")) for ref in copy if etree.QName(ref).localname in {"headerReference", "footerReference"}}
            for key, ref in inherited.items():
                if key not in current:
                    copy.insert(0, deepcopy(ref))
            sections.append((i, copy))
        return sections

    def segment(self, span: Span, preamble_end: int = 0) -> etree._Element:
        root = etree.Element(self.root.tag, attrib=dict(self.root.attrib), nsmap=self.root.nsmap)
        for child in self.root:
            if child is not self.body:
                root.append(deepcopy(child))
            else:
                root.append(etree.Element(child.tag, attrib=dict(child.attrib)))
        body = root.find("w:body", NS)
        sections = self.section_properties()
        section_map = dict(sections)
        indices = list(range(preamble_end)) + list(range(span.start, span.end))
        for i in indices:
            original = self.body[i]
            if original.tag == f"{{{W}}}sectPr":
                continue
            node = deepcopy(original)
            old_section = node.find("w:pPr/w:sectPr", NS)
            if old_section is not None:
                old_section.getparent().replace(old_section, deepcopy(section_map[i]))
            body.append(node)
        # Section properties describe the content BEFORE their position.
        final_section = next((section for i, section in sections if i >= span.end - 1), None)
        if len(body):
            last_section = body[-1].find("w:pPr/w:sectPr", NS)
            if last_section is not None:
                final_section = deepcopy(last_section)
                last_section.getparent().remove(last_section)
        if final_section is not None:
            body.append(deepcopy(final_section))
        return root

    def rels(self, part: str) -> etree._Element | None:
        path = relpath(part)
        if path not in self.names:
            return None
        if path not in self.relationships:
            self.relationships[path] = parse(self.archive.read(path))
        return deepcopy(self.relationships[path])

    def subset(self, root: etree._Element) -> tuple[set[str], dict[str, bytes]]:
        refs = {value for node in root.iter() for attr, value in node.attrib.items()
                if attr.startswith(f"{{{R}}}")}
        overrides = {DOC: xml(root)}
        keep = {DOC, "[Content_Types].xml"}
        pending = ["", DOC]
        visited = set()
        while pending:
            part = pending.pop()
            if part in visited:
                continue
            visited.add(part)
            rels = self.rels(part)
            if rels is None:
                if part == DOC and refs:
                    raise ValueError("Document references missing relationships")
                continue
            if part == DOC:
                ids = {rel.get("Id") for rel in rels}
                if refs - ids:
                    raise ValueError(f"Missing relationship IDs: {sorted(refs - ids)}")
            for rel in list(rels):
                kind = rel.get("Type", "").rsplit("/", 1)[-1]
                if part == DOC and kind in EXPLICIT and rel.get("Id") not in refs:
                    rels.remove(rel)
                    continue
                if rel.get("TargetMode") == "External":
                    continue
                target = resolve(part, rel.get("Target", ""))
                if target not in self.names:
                    raise ValueError(f"Missing package part: {target}")
                keep.add(target)
                pending.append(target)
            rp = relpath(part)
            keep.add(rp)
            overrides[rp] = xml(rels)
        types = deepcopy(self.types)
        for item in list(types):
            if item.tag == f"{{{CT}}}Override" and unquote(item.get("PartName", "")).lstrip("/") not in keep:
                types.remove(item)
        overrides["[Content_Types].xml"] = xml(types)
        return keep, overrides

    def write(self, root: etree._Element, destination: Path, personalize_part=None) -> None:
        keep, overrides = self.subset(root)
        if personalize_part:
            for name in keep:
                if name.startswith(("word/header", "word/footer")) and name.endswith(".xml"):
                    part = parse(self.archive.read(name))
                    personalize_part(part)
                    overrides[name] = xml(part)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=".span-", suffix=".docx", dir=destination.parent)
        os.close(fd)
        try:
            with ZipFile(temp, "w", compression=ZIP_DEFLATED, allowZip64=True) as output:
                for name in sorted(keep):
                    if name in overrides:
                        output.writestr(name, overrides[name])
                    else:
                        with self.archive.open(name) as source, output.open(name, "w", force_zip64=True) as target:
                            shutil.copyfileobj(source, target, length=1024 * 1024)
            validate(Path(temp))
            # Atomic publication with no overwrite, including across concurrent runs.
            os.link(temp, destination)
        finally:
            os.unlink(temp)


def validate(path: Path) -> None:
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Output ZIP checksum validation failed")
        names = set(archive.namelist())
        for name in names:
            if name.endswith(".xml") or name.endswith(".rels"):
                root = parse(archive.read(name))
                if name.endswith(".rels"):
                    part = "" if name == "_rels/.rels" else posixpath.join(posixpath.dirname(posixpath.dirname(name)), posixpath.basename(name)[:-5])
                    for rel in root:
                        if rel.get("TargetMode") != "External" and resolve(part, rel.get("Target", "")) not in names:
                            raise ValueError(f"Dangling relationship in {name}")
        root = parse(archive.read(DOC))
        if root.find("w:body", NS) is None:
            raise ValueError("Output has no document body")
