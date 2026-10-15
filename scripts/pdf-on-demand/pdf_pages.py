#!/usr/bin/env python3
"""Index local PDF text coverage, then extract explicitly selected physical pages.

SPDX-License-Identifier: MIT
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile


class PdfTaskError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def local_file_path(value: str) -> Path:
    if value.startswith(("\\\\", "//")) or (
        re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value)
        and not re.match(r"^[A-Za-z]:[\\/]", value)
    ):
        raise PdfTaskError("Use local paths, not URLs or UNC shares.")
    path = Path(value).expanduser().resolve()
    if str(path).startswith(("\\\\", "//")):
        raise PdfTaskError("Resolved paths must be local, not UNC shares.")
    return path


def protect_output(source: Path, target: Path, overwrite: bool) -> None:
    if target == source or (target.exists() and os.path.samefile(source, target)):
        raise PdfTaskError("Output must never be the input PDF or a link to it.")
    if target.suffix.lower() not in {".md", ".txt"}:
        raise PdfTaskError("Output must use .md or .txt.")
    if target.exists() and not target.is_file():
        raise PdfTaskError("Output must be a regular file path.")
    if target.exists() and not overwrite:
        raise PdfTaskError("Output exists; choose another path or pass --overwrite.")


def selected_pages(value: str, count: int) -> list[int]:
    pages: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not re.fullmatch(r"[0-9]+(?:\s*-\s*[0-9]+)?", part):
            raise PdfTaskError("Pages must be 1-based numbers or ranges, for example 1,3-5.")
        ends = [int(number.strip()) for number in part.split("-")]
        first, last = ends[0], ends[-1]
        if first < 1 or last < first or last > count:
            raise PdfTaskError(f"Page selection is outside 1-{count} or contains a reversed range.")
        pages.update(range(first, last + 1))
    return sorted(pages)


def text_for_page(page, number: int) -> str:
    try:
        return (page.extract_text() or "").strip()
    except Exception as exc:
        raise PdfTaskError(f"Text extraction failed on physical page {number}: {type(exc).__name__}.", 4) from exc


def text_status(text: str, minimum: int) -> tuple[int, str]:
    count = len(re.sub(r"\s", "", text))
    return count, "no_text" if count == 0 else ("low_text" if count < minimum else "text")


def markdown_for(reader, source: Path, args) -> str:
    count = len(reader.pages)
    if count == 0:
        raise PdfTaskError("The PDF has zero pages; no output was written.", 4)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    lines = ["# Local PDF text " + args.command, "", f"Source file: {source.name}",
             f"SHA-256: {digest}", f"Physical pages: {count}; page numbers start at 1.", "",
             "Derived text only. No OCR is performed; verify visual content against the original.", ""]
    if args.command == "index":
        lines += [f"Low-text threshold: fewer than {args.low_text} non-whitespace characters.", "",
                  "| PDF page | Characters | Status | Short preview |", "| --- | ---: | --- | --- |"]
        for number, page in enumerate(reader.pages, 1):
            text = text_for_page(page, number)
            size, status = text_status(text, args.low_text)
            preview = " ".join(text.split())[:80].replace("|", "\\|")
            lines.append(f"| {number} | {size} | {status} | {preview or '(no extractable text)'} |")
        lines += ["", "no_text and low_text are navigation warnings, not proof that a page is empty.",
                  "The index scans every page locally; it emits short previews, not the full document."]
    else:
        pages = selected_pages(args.pages, count)
        lines += ["Selected physical pages: " + ", ".join(map(str, pages)), ""]
        for number in pages:
            text = text_for_page(reader.pages[number - 1], number)
            _, status = text_status(text, args.low_text)
            lines += [f"## PDF page {number}", "", f"Text status: {status}", ""]
            if status == "no_text":
                lines += ["[No extractable text. This may be a scan or image-only page; inspect the original. No OCR was attempted.]"]
            else:
                if status == "low_text":
                    lines += ["[Little text was extracted; inspect the original before drawing conclusions.]", ""]
                lines += [text]
            lines += [""]
    return "\n".join(lines).rstrip() + "\n"


def save_output(target: Path, content: str, overwrite: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", suffix=".tmp",
                                         prefix=".pdf-pages-", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "extract"):
        command = commands.add_parser(name)
        command.add_argument("input", help="Explicit local PDF")
        command.add_argument("output", help="Derived local .md or .txt file")
        command.add_argument("--overwrite", action="store_true", help="Replace a derived output, never the source")
        command.add_argument("--low-text", type=int, default=40, help="Non-whitespace character threshold (default: 40)")
        if name == "extract":
            command.add_argument("--pages", required=True, help="1-based physical pages, e.g. 1,3-5")
    args = parser.parse_args()
    try:
        source, target = local_file_path(args.input), local_file_path(args.output)
        if not source.is_file():
            raise PdfTaskError(f"Input PDF does not exist: {source}")
        if source.suffix.lower() != ".pdf":
            raise PdfTaskError("Input must have the .pdf extension.")
        if args.low_text < 1:
            raise PdfTaskError("--low-text must be a positive integer.")
        protect_output(source, target, args.overwrite)
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise PdfTaskError("Missing pypdf dependency. Run in this Python environment: python -m pip install -r requirements.txt", 3) from exc
        with source.open("rb") as stream:
            reader = PdfReader(stream)
            if reader.is_encrypted:
                raise PdfTaskError("Encrypted PDFs are not processed. Obtain an authorized readable copy; no decryption is attempted.", 4)
            content = markdown_for(reader, source, args)
        protect_output(source, target, args.overwrite)
        save_output(target, content, args.overwrite)
    except PdfTaskError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return exc.code
    except Exception as exc:
        print(f"Error: PDF processing or local file operation failed ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 4
    print(f"{args.command} complete: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
