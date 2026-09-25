"""Sequential processing with independently logged failures and verified resume."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Callable

from app.core.config import Config
from app.core.detection import detect
from app.core.package import Package, validate
from app.core.personalization import personalize, scope_identity


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def save_json(path: Path, value: dict) -> None:
    fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def inspect(source: Path, config: Config) -> dict:
    with Package(source) as package:
        spans, duplicates = detect(package.body, config)
    return {"source": str(source), "size_bytes": source.stat().st_size,
            "profile": config.profile, "entity_kind": config.entity_kind,
            "detected": len(spans), "duplicates": duplicates,
            "spans": [span.key for span in spans]}


def process(source: Path, output: Path, config: Config, resume: bool = False,
            progress: Callable[[dict], None] | None = None) -> dict:
    source, output = source.resolve(), output.resolve()
    if source.suffix.lower() != ".docx":
        raise ValueError("Input must be a .docx file")
    fingerprint = digest(source)
    config_digest = hashlib.sha256(json.dumps(config.as_dict(), sort_keys=True).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    # One input per output directory for milestone 1. A lock avoids state/log races.
    lock = output / ".processing.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError("Output is locked. If a previous run crashed, remove .processing.lock after confirming no process is active.") from exc
    try:
        os.close(fd)
        state_path = output / "processing_state.json"
        state = {"version": 1, "source_sha256": fingerprint, "config_sha256": config_digest, "outputs": {}}
        if state_path.exists():
            old = json.loads(state_path.read_text(encoding="utf-8"))
            if not resume:
                raise ValueError("Output already contains a run. Use --resume or choose a new output folder.")
            if any(old.get(k) != state[k] for k in ("version", "source_sha256", "config_sha256")):
                raise ValueError("Source/config changed; use a new output folder")
            state = old
        with Package(source) as package:
            spans, duplicates = detect(package.body, config)
            if not spans:
                raise ValueError("No spans detected. Check regex and heading rules with --analyze.")
            targets = [output / config.filename(span.key) for span in spans]
            if any(path.resolve() == source for path in targets):
                raise ValueError("Output would overwrite the source document")
            save_json(state_path, state)
            records = []
            log_path = output / "processing_log.csv"
            with log_path.open("a", newline="", encoding="utf-8") as log:
                fields = ["timestamp", "source_file", "span_id", "status", "output_file", "error_message"]
                writer = csv.DictWriter(log, fieldnames=fields)
                if log.tell() == 0:
                    writer.writeheader()
                for index, (span, target) in enumerate(zip(spans, targets), 1):
                    row = {"timestamp": datetime.now(timezone.utc).isoformat(), "source_file": str(source),
                           "span_id": span.key, "status": "FAILED", "output_file": str(target), "error_message": ""}
                    try:
                        if span.key in duplicates:
                            raise ValueError("Duplicate Span ID; all occurrences blocked to avoid ambiguous output")
                        previous = state["outputs"].get(span.key)
                        if target.exists():
                            if resume and previous and digest(target) == previous["sha256"]:
                                validate(target)
                                row["status"] = "SKIPPED"
                            else:
                                raise FileExistsError("Existing output is unverified or changed; move it aside before retrying")
                        else:
                            root = package.segment(span, spans[0].start if config.include_preamble else 0)
                            if config.personalize_preamble:
                                personalize(root, span, spans[0].start, config.profile)
                            package.write(root, target,
                                          (lambda part: scope_identity(part, span)) if config.personalize_preamble else None)
                            state["outputs"][span.key] = {"file": target.name, "sha256": digest(target)}
                            save_json(state_path, state)
                            row["status"] = "SUCCESS"
                    except Exception as exc:
                        row["error_message"] = f"{type(exc).__name__}: {exc}"
                    writer.writerow(row)
                    log.flush()
                    records.append(row)
                    if progress:
                        progress({**row, "current": index, "total": len(spans)})
            with (output / "validation_report.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["span_id", "status", "output_file", "error_message"])
                writer.writeheader()
                writer.writerows({key: row[key] for key in writer.fieldnames} for row in records)
            summary = {"source": str(source), "source_sha256": fingerprint,
                       "profile": config.profile, "entity_kind": config.entity_kind,
                       "detected": len(spans), "generated": sum(r["status"] == "SUCCESS" for r in records),
                       "skipped": sum(r["status"] == "SKIPPED" for r in records),
                       "failed": sum(r["status"] == "FAILED" for r in records), "duplicates": duplicates}
            summary["passed"] = summary["generated"] + summary["skipped"]
            summary["source_unchanged"] = digest(source) == fingerprint
            save_json(output / "project_summary.json", summary)
            return summary
    finally:
        lock.unlink(missing_ok=True)
