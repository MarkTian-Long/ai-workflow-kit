#!/usr/bin/env python3
"""Generate a synthetic three-page PDF: normal text, little text, and image only.

SPDX-License-Identifier: MIT
"""
import argparse
from io import BytesIO
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", type=Path, help="New local synthetic PDF path")
    args = parser.parse_args()
    target = args.output.expanduser().resolve()
    if target.suffix.lower() != ".pdf":
        parser.error("Output must use .pdf.")
    if target.exists():
        parser.error("Output already exists; choose a new path.")
    try:
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.lib.utils import ImageReader
    except ImportError:
        parser.error("Install the optional fixture dependency: python -m pip install -r requirements-examples.txt")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        pdf = Canvas(stream, pagesize=(612, 792), invariant=1, pageCompression=0)
        pdf.setTitle("Synthetic PDF page-selection fixture")
        pdf.setAuthor("Synthetic example")
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(54, 730, "Synthetic PDF - text page")
        pdf.setFont("Helvetica", 12)
        for y, line in zip((690, 668, 646), (
            "Topic: alpha. These are fictional values for conversion checks.",
            "Example value: 17. This page has an extractable text layer.",
            "Physical page 1 is different from a document's printed page label.",
        )):
            pdf.drawString(54, y, line)
        pdf.showPage()
        pdf.setFont("Helvetica", 12)
        pdf.drawString(54, 730, "Short note")
        pdf.showPage()
        # A generated raster pattern without a text layer, not a real scanned document.
        pixels = bytes(component for y in range(32) for x in range(64)
                       for component in ((30, 90, 170) if (x // 8 + y // 8) % 2 else (220, 232, 245)))
        image = ImageReader(BytesIO(b"P6\n64 32\n255\n" + pixels))
        pdf.drawImage(image, 54, 520, width=384, height=192)
        pdf.showPage()
        pdf.save()
    print(f"Synthetic PDF created: {target}")


if __name__ == "__main__":
    main()
