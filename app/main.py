import argparse
import json
from pathlib import Path
import sys

from app.core.config import Config
from app.services.processing import inspect, process


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LiPowerline Report Splitter — local DOCX processing")
    parser.add_argument("--input", required=True, type=Path, help="Consolidated DOCX (read-only)")
    parser.add_argument("--output", type=Path, help="Dedicated output directory")
    parser.add_argument("--config", type=Path, help="Parser YAML; auto-detect known report formats if omitted")
    parser.add_argument("--analyze", action="store_true", help="Preview detected spans without writing outputs")
    parser.add_argument("--resume", action="store_true", help="Skip verified outputs and retry missing outputs")
    args = parser.parse_args(argv)
    if not args.analyze and args.output is None:
        parser.error("--output is required unless --analyze is used")
    try:
        config = Config.for_source(args.input, args.config)
        if args.analyze:
            result = inspect(args.input, config)
        else:
            def progress(row: dict) -> None:
                print(f"[{row['current']}/{row['total']}] {row['span_id']} {row['status']} {row['error_message']}", file=sys.stderr)
            result = process(args.input, args.output, config, args.resume, progress)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result.get("failed") or result.get("source_unchanged") is False or result.get("detected") == 0 or result.get("duplicates") else 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
