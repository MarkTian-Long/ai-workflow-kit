#!/usr/bin/env python3
"""Compare a pinned relation baseline with annotated SVG declarations, offline.

This checks node text and directed, labelled edges, NOT their drawn geometry,
visibility, factual correctness, or approval. Run check-layout and inspect the
final container separately. No Mermaid parser, fonts, browser, or network here.
Exit: 0 declaration-match; 2 revise; 3 unsupported coverage; 1 invalid invocation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

VERSION = "0.1.0"
LIMIT = 8 * 1024 * 1024
SVG = "{http://www.w3.org/2000/svg}"


class Unsupported(ValueError):
    """The SVG cannot be inspected with this bounded annotation contract."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def label(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Labels must be strings")
    # Only line wrapping is presentation-only; spaces, negation and case remain.
    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "")


def graph(value: object) -> tuple[dict[str, str], Counter]:
    if not isinstance(value, dict):
        raise ValueError("Graph must be a JSON object")
    nodes, edges = value.get("nodes"), value.get("edges")
    if not isinstance(nodes, dict) or not nodes or not isinstance(edges, list) or not edges:
        raise ValueError("Graph requires nonempty nodes object and edges array")
    clean_nodes = {}
    for key, text in nodes.items():
        if not isinstance(key, str) or not key or key != key.strip():
            raise ValueError("Node IDs must be nonempty trimmed strings")
        normalized = label(text)
        if not normalized.strip():
            raise ValueError(f"Empty node label: {key}")
        clean_nodes[key] = normalized
    clean_edges = []
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {"from", "to", "label"}:
            raise ValueError("Each edge must contain exactly from, to and label")
        a, b = edge["from"], edge["to"]
        if not isinstance(a, str) or not isinstance(b, str) or a not in nodes or b not in nodes:
            raise ValueError("An edge references an unknown node")
        clean_edges.append((a, b, label(edge["label"])))
    return clean_nodes, Counter(clean_edges)


def svg_graph(data: bytes) -> dict:
    if len(data) > LIMIT:
        raise ValueError("SVG exceeds the 8 MiB inspection limit")
    text = data.decode("utf-8-sig")
    if re.search(r"<!DOCTYPE|<!ENTITY|<\?", text, re.I):
        raise Unsupported("DTD, entities and processing instructions are unsupported")
    root = ET.fromstring(text)
    if root.tag != SVG + "svg":
        raise Unsupported("Expected a namespaced SVG root")
    nodes, edges, edge_ids = {}, [], set()
    graphical = {"rect", "circle", "ellipse", "path", "line", "polyline", "polygon", "text", "use", "image"}
    forbidden = {"script", "foreignObject", "iframe", "animate", "animateMotion", "animateTransform", "set", "use", "image", "a"}

    def local(element):
        return element.tag.removeprefix(SVG)

    # XML is never executed. Active or external content is nevertheless refused.
    for element in root.iter():
        if not element.tag.startswith(SVG) or local(element) in forbidden:
            raise Unsupported("Unsupported SVG element or namespace")
        for key, val in element.attrib.items():
            name = key.rsplit("}", 1)[-1].lower()
            if name.startswith("on") or name in {"href", "src"}:
                raise Unsupported("Active content or resource reference is unsupported")
            for resource in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", val, re.I):
                if not resource.startswith("#"):
                    raise Unsupported("Only local fragment resources are supported")
            if re.search(r"javascript:|@import|@font-face", val, re.I):
                raise Unsupported("Active or external style is unsupported")
        styles = " ".join([element.attrib.get("style", ""), element.text or ""])
        if re.search(r"@import|@font-face|javascript:", styles, re.I):
            raise Unsupported("External or active stylesheet is unsupported")
        for resource in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", styles, re.I):
            if not resource.startswith("#"):
                raise Unsupported("Only local fragment resources are supported")

    def text_of(group):
        explicit = [el for el in group.iter(SVG + "text") if el.get("data-visual-label") == "true"]
        texts = explicit or list(group.iter(SVG + "text"))
        # title/desc/data-label never substitute for drawn text declarations.
        return "".join("".join(el.itertext()) for el in texts)

    def walk(element, owner=None, decoration=False, definitions=False):
        tag = local(element)
        definitions = definitions or tag in {"defs", "marker"}
        decoration = decoration or element.get("data-visual-decoration") == "true"
        roles = [key for key in ("data-visual-node", "data-visual-edge", "data-visual-region") if key in element.attrib]
        if len(roles) > 1:
            raise Unsupported("One element has conflicting graph roles")
        if roles and definitions:
            raise Unsupported("Graph declarations cannot be hidden in definitions")
        if roles:
            if owner in {"node", "edge"} or decoration or tag != "g":
                raise Unsupported("Graph groups cannot be nested in nodes, edges or decoration")
            owner = roles[0].removeprefix("data-visual-")
            key = element.get(roles[0])
            if not key or key != key.strip():
                raise ValueError("Graph group IDs must be nonempty and trimmed")
            if owner == "node":
                if key in nodes:
                    raise ValueError("Duplicate SVG node ID: " + key)
                nodes[key] = text_of(element)
            elif owner == "edge":
                if key in edge_ids:
                    raise ValueError("Duplicate SVG edge ID: " + key)
                edge_ids.add(key)
                lines = [el for el in element.iter() if el.get("data-visual-line") == "true"]
                if not lines or any(local(el) not in {"path", "line", "polyline"} for el in lines):
                    raise Unsupported("Every edge needs a marked path, line or polyline")
                edges.append({"from": element.get("data-from"), "to": element.get("data-to"), "label": text_of(element)})
        accounted = owner in {"node", "edge"} or (owner == "region" and element.get("data-visual-shape") == "true")
        if tag in graphical and not (definitions or decoration or accounted):
            raise Unsupported("Unaccounted drawing element; annotate its role rather than silently ignoring it")
        for child in element:
            walk(child, owner, decoration, definitions)

    walk(root)
    if not nodes or not edges:
        raise Unsupported("No complete annotated node/edge coverage; do not treat zero findings as a match")
    result = {"nodes": nodes, "edges": edges}
    graph(result)
    return result


def compare(baseline: dict, candidate: dict) -> dict:
    a, ae = graph(baseline)
    b, be = graph(candidate)
    differences = {
        "missing_nodes": sorted(a.keys() - b.keys()),
        "extra_nodes": sorted(b.keys() - a.keys()),
        "changed_labels": sorted(key for key in a.keys() & b.keys() if a[key] != b[key]),
        "missing_edges": sorted((ae - be).elements()),
        "extra_edges": sorted((be - ae).elements()),
    }
    return {
        "checker_version": VERSION,
        "status": "revise" if any(differences.values()) else "declaration-match",
        "scope": "annotated SVG node text and directed labelled edge declarations only",
        "differences": differences,
        "node_count": len(b), "edge_count": sum(be.values()),
        "visual_review_performed": False, "platform_verified": False,
        "limits": ["Baseline approval and factual correctness are not verified.",
                   "CSS visibility, glyphs, geometry and actual arrow endpoints are not verified.",
                   "Run check-layout and inspect the final delivery container separately."],
    }


def read_bytes(path: Path) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("Input exceeds the 8 MiB inspection limit")
    return data


def write_report(path: Path, data: bytes, inputs: list[Path], replace: bool) -> None:
    if path.is_symlink() or any(path.resolve() == p.resolve() or
            (path.exists() and p.exists() and path.samefile(p)) for p in inputs):
        raise ValueError("Report must not alias any input or use a symlink")
    if path.exists():
        if path.read_bytes() == data:
            return
        if not replace:
            raise ValueError("Report differs; explicit --replace-report is required")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".graph-qa-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            # Atomic create-only publication: a concurrent writer is not replaced.
            os.link(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Approved nodes/edges JSON; the R2 source-graph.json shape is accepted")
    parser.add_argument("svg", type=Path)
    parser.add_argument("--baseline-sha256", required=True, help="Pin the independently reviewed baseline bytes")
    parser.add_argument("--source", type=Path, help="Optional immutable source; must match baseline.sourceSha256")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--replace-report", action="store_true")
    options = parser.parse_args(argv)
    try:
        raw, svg = read_bytes(options.baseline), read_bytes(options.svg)
        if not re.fullmatch(r"[0-9a-fA-F]{64}", options.baseline_sha256) or digest(raw) != options.baseline_sha256.lower():
            raise ValueError("Baseline SHA256 does not match the pinned review baseline")
        baseline = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object)
        graph(baseline)
        source_verified = False
        if options.source:
            if digest(read_bytes(options.source)) != baseline.get("sourceSha256"):
                raise ValueError("Source SHA256 is absent or stale")
            source_verified = True
        result = compare(baseline, svg_graph(svg))
        result.update(baseline_sha256=digest(raw), svg_sha256=digest(svg), source_hash_verified=source_verified)
        data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if options.report:
            inputs = [options.baseline, options.svg] + ([options.source] if options.source else [])
            write_report(options.report, data, inputs, options.replace_report)
        sys.stdout.write(data.decode("utf-8"))
        return 0 if result["status"] == "declaration-match" else 2
    except (Unsupported, ValueError, OSError, ET.ParseError) as error:
        unsupported = isinstance(error, Unsupported)
        print(json.dumps({"status": "unsupported" if unsupported else "error", "message": str(error),
                          "visual_review_performed": False, "platform_verified": False}, ensure_ascii=False))
        return 3 if unsupported else 1


if __name__ == "__main__":
    raise SystemExit(main())
