#!/usr/bin/env python3
"""Convert an explicitly selected local document to Markdown.

SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile


SUPPORTED = {".html", ".htm", ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".csv", ".txt", ".md"}


class ConversionError(Exception):
    def __init__(self, message: str, code: int = 2):
        super().__init__(message)
        self.code = code


def local_path(value: str) -> Path:
    """Reject URLs and UNC shares; resolve ordinary local filesystem paths."""
    if value.startswith(("\\\\", "//")) or (
        re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value)
        and not re.match(r"^[A-Za-z]:[\\/]", value)
    ):
        raise ConversionError("Use a local file path; URLs and UNC shares are not accepted.")
    path = Path(value).expanduser().resolve()
    if str(path).startswith(("\\\\", "//")):
        raise ConversionError("Resolved paths must be local; UNC shares are not accepted.")
    return path


def check_destination(source: Path, destination: Path, overwrite: bool) -> None:
    if source == destination or (
        destination.exists() and os.path.samefile(source, destination)
    ):
        raise ConversionError("Output must differ from input, including links to the same file.")
    if destination.exists() and not destination.is_file():
        raise ConversionError("Output must be a file path, not a directory or special file.")
    if destination.exists() and not overwrite:
        raise ConversionError("Output already exists; choose a new path or pass --overwrite.")


def convert_document(source: Path) -> str:
    try:
        from markitdown import MarkItDown
        from markitdown.converters import (
            CsvConverter,
            DocxConverter,
            HtmlConverter,
            PdfConverter,
            PlainTextConverter,
            PptxConverter,
            XlsConverter,
            XlsxConverter,
        )
    except ImportError as exc:
        raise ConversionError(
            "Missing conversion dependency. In this Python environment run: "
            "python -m pip install -r requirements.txt "
            f"(unavailable module: {exc.name or 'markitdown'}).",
            3,
        ) from exc

    # Register document converters explicitly: no plugins, audio transcription,
    # URL-specific converters, cloud endpoints, or LLM clients are enabled.
    converter = MarkItDown(enable_builtins=False, enable_plugins=False)
    for converter_class in (
        PlainTextConverter, HtmlConverter, CsvConverter, PdfConverter,
        DocxConverter, PptxConverter, XlsConverter, XlsxConverter,
    ):
        converter.register_converter(converter_class())
    result = converter.convert_local(str(source))
    markdown = result.text_content
    if not markdown.strip():
        raise ConversionError(
            "Conversion returned no text; image-only or scanned files may need OCR. "
            "No output was written.",
            4,
        )
    return markdown.rstrip() + "\n"


def write_markdown(destination: Path, markdown: str, overwrite: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        # Exclusive creation also rejects a file created after the initial check.
        with destination.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(markdown)
        return

    # Replace the directory entry instead of following an existing hard/symbolic
    # link while truncating a file. Conversion failures preserve the old output.
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", suffix=".tmp",
            prefix=".document-conversion-", dir=destination.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(markdown)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", help="Explicit local source file")
    parser.add_argument("output", help="Local Markdown destination")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output; never the input")
    args = parser.parse_args()
    try:
        source = local_path(args.input)
        destination = local_path(args.output)
        if not source.is_file():
            raise ConversionError(f"Input is not a file: {source}")
        if source.suffix.lower() not in SUPPORTED:
            raise ConversionError("Unsupported document extension. Supported: " + ", ".join(sorted(SUPPORTED)))
        check_destination(source, destination, args.overwrite)
        markdown = convert_document(source)
        # Recheck after conversion in case an output was created meanwhile.
        check_destination(source, destination, args.overwrite)
        write_markdown(destination, markdown, args.overwrite)
    except ConversionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return exc.code
    except (OSError, ValueError) as exc:
        print(f"Error: local file operation failed: {exc}", file=sys.stderr)
        return 4
    except Exception as exc:
        print(
            f"Error: conversion failed ({type(exc).__name__}): {exc}\n"
            "Check the format and its optional dependencies; inspect the original file.",
            file=sys.stderr,
        )
        return 4
    print(f"Markdown written: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
