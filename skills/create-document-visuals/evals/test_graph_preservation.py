"""Declaration-level regression tests. SVG fixtures are not visual approvals."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.sax.saxutils import escape

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_graph_preservation.py"
spec = importlib.util.spec_from_file_location("graph_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def model():
    return {"nodes": {"R": "共同理解", "D": "需要媒体？", "TX": "文字回答", "M": "媒体生成路径",
                      "G": "模型内生成", "P": "系统调用", "O": "媒体结果"},
            "edges": [{"from": a, "to": b, "label": text} for a, b, text in [
                ("R", "D", ""), ("D", "TX", "不需要"), ("D", "M", "需要"),
                ("M", "G", ""), ("M", "P", ""), ("G", "O", ""), ("P", "O", "")]]}


def svg_of(value):
    nodes = ''.join(f'<g data-visual-node="{key}"><rect data-visual-shape="true" width="100" height="30"/>'
                    f'<text>{escape(text)}</text></g>' for key, text in value["nodes"].items())
    edges = ''.join(f'<g data-visual-edge="edge-{i}" data-from="{e["from"]}" data-to="{e["to"]}">'
                    '<path data-visual-line="true" d="M0 0L0 1"/>'
                    + (f'<text>{escape(e["label"])}</text>' if e["label"] else '') + '</g>'
                    for i, e in enumerate(value["edges"]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">' + nodes + edges + '</svg>').encode()


class GraphTests(unittest.TestCase):
    def check(self, value):
        return guard.compare(model(), guard.svg_graph(svg_of(value)))

    def test_original_and_metadata_record(self):
        value = model()
        value.update(schemaVersion="source-graph-static-v1", authorApproved=False, textBounds=[])
        result = guard.compare(value, guard.svg_graph(svg_of(value)))
        self.assertEqual(result["status"], "declaration-match")
        self.assertFalse(result["visual_review_performed"])
        self.assertFalse(result["platform_verified"])

    def test_reordering_is_not_a_logic_change(self):
        value = model()
        value["nodes"] = dict(reversed(list(value["nodes"].items())))
        value["edges"].reverse()
        self.assertEqual(self.check(value)["status"], "declaration-match")

    def test_two_node_graph_not_hardcoded_to_seven_or_thirteen(self):
        value = {"nodes": {"first_1": "开始", "last-2": "完成"},
                 "edges": [{"from": "first_1", "to": "last-2", "label": ""}]}
        self.assertEqual(guard.compare(value, guard.svg_graph(svg_of(value)))["status"], "declaration-match")

    def test_three_peer_outputs_are_rejected(self):
        value = model()
        value["nodes"].pop("D")
        value["nodes"].pop("M")
        value["edges"] = [{"from": "R", "to": target, "label": ""} for target in ["TX", "G", "P"]] + value["edges"][-2:]
        self.assertEqual(self.check(value)["status"], "revise")

    def test_same_counts_wrong_direction_is_rejected(self):
        value = model()
        value["edges"][-1].update({"from": "O", "to": "P"})
        result = self.check(value)
        self.assertEqual(result["edge_count"], 7)
        self.assertTrue(result["differences"]["missing_edges"])

    def test_swapped_conditions_are_rejected(self):
        value = model()
        value["edges"][1]["label"], value["edges"][2]["label"] = value["edges"][2]["label"], value["edges"][1]["label"]
        self.assertEqual(self.check(value)["status"], "revise")

    def test_negation_and_spaces_are_not_removed(self):
        for text in ["需要", "不 需要"]:
            value = model()
            value["edges"][1]["label"] = text
            self.assertEqual(self.check(value)["status"], "revise")

    def test_label_changes_are_rejected(self):
        value = model()
        value["nodes"]["P"] = "人工调用"
        self.assertEqual(self.check(value)["differences"]["changed_labels"], ["P"])

    def test_line_wrapping_preserves_text(self):
        xml = svg_of(model()).replace('<text>模型内生成</text>'.encode(), '<text>模型内</text><text>生成</text>'.encode())
        self.assertEqual(guard.compare(model(), guard.svg_graph(xml))["status"], "declaration-match")

    def test_explicit_label_excludes_supplementary_note(self):
        xml = svg_of(model()).replace('<text>共同理解</text>'.encode(),
             '<text data-visual-label="true">共同理解</text><text>辅助说明</text>'.encode())
        self.assertEqual(guard.compare(model(), guard.svg_graph(xml))["status"], "declaration-match")

    def test_duplicate_edges_are_not_deduplicated(self):
        value = model()
        value["edges"].append(deepcopy(value["edges"][0]))
        self.assertEqual(len(self.check(value)["differences"]["extra_edges"]), 1)

    def test_unknown_endpoint_is_rejected(self):
        value = model()
        value["edges"][0]["to"] = "missing"
        with self.assertRaises(ValueError):
            self.check(value)

    def test_duplicate_node_and_edge_ids_are_rejected(self):
        for old, new in [(b'data-visual-node="D"', b'data-visual-node="R"'),
                         (b'data-visual-edge="edge-1"', b'data-visual-edge="edge-0"')]:
            with self.assertRaises(ValueError):
                guard.svg_graph(svg_of(model()).replace(old, new))

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"nodes":{"A":"first","A":"second"}}', object_pairs_hook=guard.unique_object)

    def test_empty_graph_is_not_a_match(self):
        with self.assertRaises(ValueError):
            guard.compare({"nodes": {}, "edges": []}, {"nodes": {}, "edges": []})

    def test_unmarked_line_is_not_silently_ignored(self):
        xml = svg_of(model()).replace(b'</svg>', b'<path d="M0 0L20 20"/></svg>')
        with self.assertRaises(guard.Unsupported):
            guard.svg_graph(xml)

    def test_unmarked_line_in_region_is_rejected(self):
        xml = svg_of(model()).replace(b'</svg>', b'<g data-visual-region="region"><path d="M0 0L20 20"/></g></svg>')
        with self.assertRaises(guard.Unsupported):
            guard.svg_graph(xml)

    def test_explicit_decoration_is_allowed(self):
        xml = svg_of(model()).replace(b'</svg>', b'<text data-visual-decoration="true">Title</text></svg>')
        self.assertEqual(guard.compare(model(), guard.svg_graph(xml))["status"], "declaration-match")

    def test_metadata_cannot_substitute_for_label(self):
        xml = svg_of(model()).replace('<text>不需要</text>'.encode(), '<title>不需要</title>'.encode())
        self.assertEqual(guard.compare(model(), guard.svg_graph(xml))["status"], "revise")

    def test_metadata_cannot_substitute_for_a_line(self):
        xml = svg_of(model()).replace(b'<path data-visual-line="true" d="M0 0L0 1"/>', b'', 1)
        with self.assertRaises(guard.Unsupported):
            guard.svg_graph(xml)

    def test_active_or_external_svg_is_rejected(self):
        for extra in [b'<script/>', b'<image href="file:///private.png"/>', b'<rect onload="x"/>',
                      b'<style>@import "https://invalid/style";</style>',
                      b'<g style="fill:url(https://invalid/paint)"/>']:
            with self.assertRaises(guard.Unsupported):
                guard.svg_graph(svg_of(model()).replace(b'</svg>', extra + b'</svg>'))
        with self.assertRaises(guard.Unsupported):
            guard.svg_graph(b'<!DOCTYPE svg>' + svg_of(model()))

    def test_geometry_is_explicitly_not_claimed(self):
        # The declared endpoints stay the same even if the actual path changes.
        xml = svg_of(model()).replace(b'd="M0 0L0 1"', b'd="M0 0L9999 9999"')
        result = guard.compare(model(), guard.svg_graph(xml))
        self.assertEqual(result["status"], "declaration-match")
        self.assertFalse(result["visual_review_performed"])
        self.assertIn("geometry", ' '.join(result["limits"]))


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.baseline = self.root / 'source-graph.json'
        self.svg = self.root / 'candidate.svg'
        self.report = self.root / 'graph.qa.json'
        self.baseline.write_text(json.dumps(model(), ensure_ascii=False), encoding='utf-8')
        self.svg.write_bytes(svg_of(model()))

    def args(self):
        return [str(self.baseline), str(self.svg), '--baseline-sha256', guard.digest(self.baseline.read_bytes())]

    def run_main(self, extras=()):
        stream = io.StringIO()
        with redirect_stdout(stream):
            status = guard.main(self.args() + list(extras))
        return status, json.loads(stream.getvalue())

    def test_hashes_pin_the_actual_bytes(self):
        code, result = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual(result['svg_sha256'], guard.digest(self.svg.read_bytes()))
        self.assertFalse(result['source_hash_verified'])

    def test_mismatch_exit_code_two(self):
        value = model()
        value['edges'][1]['label'] = '需要'
        self.svg.write_bytes(svg_of(value))
        self.assertEqual(self.run_main()[0], 2)

    def test_unsupported_exit_code_three(self):
        self.svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>hello</text></svg>')
        self.assertEqual(self.run_main()[0], 3)

    def test_optimized_python_does_not_disable_validation(self):
        value = model()
        value['edges'][1]['label'] = '需要'
        self.svg.write_bytes(svg_of(value))
        run = subprocess.run([sys.executable, '-O', str(SCRIPT), *self.args()], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2, run.stdout + run.stderr)

    def test_old_report_preserved_after_bad_baseline(self):
        self.report.write_text('old report')
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = guard.main([str(self.baseline), str(self.svg), '--baseline-sha256', '0' * 64,
                               '--report', str(self.report), '--replace-report'])
        self.assertEqual(code, 1)
        self.assertEqual(self.report.read_text(), 'old report')

    def test_no_silent_overwrite_and_idempotent_report(self):
        self.assertEqual(self.run_main(['--report', str(self.report)])[0], 0)
        first = self.report.read_bytes()
        self.assertEqual(self.run_main(['--report', str(self.report)])[0], 0)
        self.report.write_text('prior')
        self.assertEqual(self.run_main(['--report', str(self.report)])[0], 1)
        self.assertEqual(self.report.read_text(), 'prior')
        self.assertEqual(self.run_main(['--report', str(self.report), '--replace-report'])[0], 0)
        self.assertEqual(first, self.report.read_bytes())

    def test_report_cannot_overwrite_source_or_hardlink(self):
        original = self.baseline.read_bytes()
        self.assertEqual(self.run_main(['--report', str(self.baseline), '--replace-report'])[0], 1)
        os.link(self.baseline, self.report)
        self.assertEqual(self.run_main(['--report', str(self.report), '--replace-report'])[0], 1)
        self.assertEqual(self.baseline.read_bytes(), original)

    def test_report_symlink_is_rejected(self):
        self.report.symlink_to(self.baseline)
        self.assertEqual(self.run_main(['--report', str(self.report), '--replace-report'])[0], 1)

    def test_source_hash_is_checked_not_inferred_from_filename(self):
        source = self.root / 'flow.mmd'
        source.write_text('immutable definition')
        value = model()
        value['sourceSha256'] = guard.digest(source.read_bytes())
        self.baseline.write_text(json.dumps(value))
        code, result = self.run_main(['--source', str(source)])
        self.assertEqual(code, 0)
        self.assertTrue(result['source_hash_verified'])
        source.write_text('changed definition')
        self.assertEqual(self.run_main(['--source', str(source)])[0], 1)


if __name__ == '__main__':
    unittest.main()
