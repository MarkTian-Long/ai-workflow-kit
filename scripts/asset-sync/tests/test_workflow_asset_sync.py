import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

source = Path(os.environ.get("WORKFLOW_ASSET_SYNC_SOURCE", str(Path(__file__).resolve().parents[1] / "workflow_asset_sync.py")))
spec = importlib.util.spec_from_file_location("sync", source)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class SyncBoundaryTests(unittest.TestCase):
    def setUp(self):
        fixtures = Path(__file__).resolve().parent / "test-fixtures"
        fixtures.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=fixtures)
        if not Path(self.temp.name).resolve().is_relative_to(fixtures.resolve()):
            raise RuntimeError("Test cleanup target escapes fixture workspace")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "content").mkdir()
        (self.root / "content" / "guide.md").write_text("# A reusable guide\n", encoding="utf-8")
        self.cp = self.root / "catalog.json"
        self.bp = self.root / "baseline.json"
        self.c = {"schema_version": 1, "runs_root": "runs", "private_patterns": ["SECRET_EXAMPLE"],
            "targets": {"kit": {"repository": "example/kit", "branch": "main", "enabled": True,
                "mode": "reviewed-snapshot", "license": "MIT", "state_path": "state.json",
                "allowlist_path": "publication-allowlist.json", "authorization_note": "test scope"}},
            "assets": [{"id": "guide", "target": "kit", "kind": "sop", "source_root": "content",
                "license": "MIT", "status": "approved", "authorization_note": "synthetic original",
                "members": [{"source": "guide.md", "destination": "sops/guide.md"}]}]}
        self.b = {"repository": "example/kit", "branch": "main", "commit": "a" * 40,
            "tree_sha": "b" * 40, "files": {"community.md": "c" * 40}}
        self.save()
        s.write_json(self.bp, self.b)

    def save(self):
        for a in self.c["assets"]:
            a["approved_policy_sha256"] = s.asset_policy(a)
        for t in self.c["targets"].values():
            t["approved_policy_sha256"] = s.target_policy(t)
        s.write_json(self.cp, self.c)

    def prepare(self):
        return Path(s.prepare(self.cp, "kit", self.bp)["run"])

    def approve(self, run):
        s.review(run, "Reviewed synthetic rights, dependencies, behavior and exact diff", ["synthetic check"])

    def test_preserves_remote_unowned_and_reads_complete_tree(self):
        run = self.prepare()
        self.approve(run)
        s.upload_plan(run)
        m = s.read_json(run / "manifest.json")
        self.assertEqual(m["expected_tree"]["community.md"], "c" * 40)
        r = {"repository": "example/kit", "branch": "main", "parent": "a" * 40,
            "commit": "d" * 40, "head_after": "d" * 40, "tree_sha": "e" * 40, "files": m["expected_tree"]}
        s.write_json(self.root / "readback.json", r)
        self.assertTrue(s.receipt(run, self.root / "readback.json")["state_advanced"])
        self.b.update(commit="d" * 40, tree_sha="e" * 40, files=m["expected_tree"])
        s.write_json(self.bp, self.b)
        self.assertEqual(s.prepare(self.cp, "kit", self.bp)["status"], "no-change")

    def test_missing_source_never_means_delete(self):
        (self.root / "content" / "guide.md").unlink()
        with self.assertRaisesRegex(s.SyncError, "missing is never"):
            self.prepare()

    def test_markdown_fenced_examples_are_not_live_resources(self):
        for fence in ["```", "~~~~"]:
            files = {"guide.md": (f"{fence}markdown\n![example](missing.svg)\n{fence}\n[actual](real.md)\n").encode(), "real.md": b"# real\n"}
            self.assertEqual(s.validate_files(files, [])["local_references"], 1)

    def test_fenced_code_still_gets_privacy_scan(self):
        with self.assertRaisesRegex(s.SyncError, "Private/secret"):
            s.validate_files({"guide.md": b"```\nSECRET_EXAMPLE\n```\n"}, ["SECRET_EXAMPLE"])

    def test_missing_live_link_outside_fence_is_rejected(self):
        with self.assertRaisesRegex(s.SyncError, "Missing packaged reference"):
            s.validate_files({"guide.md": b"```\n[example](ignored.md)\n```\n[actual](missing.md)\n"}, [])

    def test_markdown_packaged_directory_link_is_supported(self):
        files = {"guide.md": b"[vendor](assets/vendor/)\n", "assets/vendor/LICENSE": b"license"}
        self.assertEqual(s.validate_files(files, [])["local_references"], 1)

    def test_missing_directory_and_directory_image_are_rejected(self):
        with self.assertRaisesRegex(s.SyncError, "Missing packaged reference"):
            s.validate_files({"guide.md": b"[missing](absent/)\n"}, [])
        with self.assertRaisesRegex(s.SyncError, "Missing packaged reference"):
            s.validate_files({"picture.svg": b'<svg xmlns="http://www.w3.org/2000/svg"><image href="assets/"/></svg>', "assets/LICENSE": b"license"}, [])

    def use_source_manifest(self):
        data = (self.root / "content" / "guide.md").read_bytes()
        s.write_json(self.root / "content" / "release.json", {"files": {
            "sops/guide.md": {"bytes": len(data), "sha256": s.digest(data)}}})
        self.c["assets"][0]["members"].append({"source": "release.json", "destination": "release.json"})
        self.c["targets"]["kit"].update(allowlist_mode="source-sha256-manifest", allowlist_path="release.json")
        self.save()

    def test_product_manifest_preserved_without_extra_members(self):
        self.use_source_manifest()
        run = self.prepare()
        m = s.read_json(run / "manifest.json")
        self.assertEqual(set(m["files"]), {"sops/guide.md", "release.json"})
        self.assertEqual((run / "files/release.json").read_bytes(), (self.root / "content/release.json").read_bytes())

    def test_product_manifest_rejects_stale_bytes(self):
        self.use_source_manifest()
        (self.root / "content/guide.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(s.SyncError, "exact prepared bytes/members"):
            self.prepare()

    def test_product_manifest_rejects_missing_manifest(self):
        self.c["targets"]["kit"]["allowlist_mode"] = "source-sha256-manifest"
        self.save()
        with self.assertRaisesRegex(s.SyncError, "manifest missing"):
            self.prepare()

    def test_unknown_allowlist_mode_rejected(self):
        self.c["targets"]["kit"]["allowlist_mode"] = "disable-checks"
        self.save()
        with self.assertRaisesRegex(s.SyncError, "Unknown allowlist mode"):
            self.prepare()

    def test_source_drift_requires_reprepare(self):
        run = self.prepare()
        (self.root / "content" / "guide.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(s.SyncError, "Source changed"):
            self.approve(run)

    def test_missing_review_blocks_upload(self):
        with self.assertRaises(FileNotFoundError):
            s.upload_plan(self.prepare())

    def test_payload_tampering_blocks_review(self):
        run = self.prepare()
        (run / "files" / "sops" / "guide.md").write_text("tampered", encoding="utf-8")
        with self.assertRaisesRegex(s.SyncError, "payload changed"):
            self.approve(run)

    def test_catalog_policy_change_requires_approval(self):
        self.c["assets"][0]["members"][0]["destination"] = "other.md"
        s.write_json(self.cp, self.c)
        with self.assertRaisesRegex(s.SyncError, "Asset boundary changed"):
            self.prepare()

    def test_new_destination_requires_target_approval(self):
        self.c["targets"]["kit"]["repository"] = "example/another"
        s.write_json(self.cp, self.c)
        with self.assertRaisesRegex(s.SyncError, "Target scope changed"):
            self.prepare()

    def test_path_escape_is_rejected(self):
        self.c["assets"][0]["members"][0]["destination"] = "../leak.md"
        self.save()
        with self.assertRaisesRegex(s.SyncError, "escapes"):
            self.prepare()

    def test_private_content_is_rejected(self):
        (self.root / "content" / "guide.md").write_text("SECRET_EXAMPLE", encoding="utf-8")
        with self.assertRaisesRegex(s.SyncError, "Private/secret"):
            self.prepare()

    def test_missing_references_are_rejected(self):
        (self.root / "content" / "guide.md").write_text("[missing](absent.md)", encoding="utf-8")
        with self.assertRaisesRegex(s.SyncError, "Missing packaged reference"):
            self.prepare()

    def test_adapter_drift_is_rejected(self):
        self.c["assets"][0]["members"][0]["transforms"] = [{"op": "replace", "old": "absent", "new": "updated"}]
        self.save()
        with self.assertRaisesRegex(s.SyncError, "Adapter drift"):
            self.prepare()

    def test_owned_remote_changes_block_overwrite(self):
        s.write_json(self.root / "state.json", {"repository": "example/kit", "commit": "a" * 40,
            "managed_files": {"sops/guide.md": "f" * 40}})
        self.b["files"]["sops/guide.md"] = "1" * 40
        s.write_json(self.bp, self.b)
        with self.assertRaisesRegex(s.SyncError, "Remote owned files changed"):
            self.prepare()

    def test_unmanaged_target_collision_requires_adoption(self):
        self.b["files"]["sops/guide.md"] = "1" * 40
        s.write_json(self.bp, self.b)
        with self.assertRaisesRegex(s.SyncError, "baseline adoption"):
            self.prepare()

    def test_retired_file_requires_explicit_removal(self):
        s.write_json(self.root / "state.json", {"managed_files": {"retired.md": "f" * 40}})
        with self.assertRaisesRegex(s.SyncError, "explicit retirement"):
            self.prepare()

    def test_stale_receipt_does_not_regress_latest_state(self):
        run = self.prepare()
        self.approve(run)
        m = s.read_json(run / "manifest.json")
        s.write_json(self.root / "state.json", {"commit": "f" * 40})
        r = {"repository": "example/kit", "branch": "main", "parent": "a" * 40,
            "commit": "d" * 40, "head_after": "d" * 40, "tree_sha": "e" * 40, "files": m["expected_tree"]}
        s.write_json(self.root / "readback.json", r)
        self.assertFalse(s.receipt(run, self.root / "readback.json")["state_advanced"])
        self.assertEqual(s.read_json(self.root / "state.json")["commit"], "f" * 40)

    def test_partial_readback_is_not_success(self):
        run = self.prepare()
        self.approve(run)
        r = {"repository": "example/kit", "branch": "main", "parent": "a" * 40,
            "commit": "d" * 40, "head_after": "d" * 40, "files": {}}
        s.write_json(self.root / "readback.json", r)
        with self.assertRaisesRegex(s.SyncError, "complete expected tree"):
            s.receipt(run, self.root / "readback.json")

    def test_no_change_does_not_allow_review_or_commit(self):
        run = self.prepare()
        self.b["files"] = s.read_json(run / "manifest.json")["expected_tree"]
        s.write_json(self.bp, self.b)
        run = self.prepare()
        with self.assertRaisesRegex(s.SyncError, "No-change"):
            self.approve(run)

    def test_external_runtime_html_resource_is_refused(self):
        with self.assertRaisesRegex(s.SyncError, "External runtime resource"):
            s.validate_files({"index.html": b'<script src="https://example.com/a.js"></script>'}, [])

    def test_namespaced_svg_external_reference_is_refused(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><image xlink:href="https://example.com/image.png"/></svg>'
        with self.assertRaisesRegex(s.SyncError, "External runtime resource"):
            s.validate_files({"diagram.svg": svg}, [])

    def test_namespaced_svg_local_reference_must_exist(self):
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><use xlink:href="missing.svg#node"/></svg>'
        with self.assertRaisesRegex(s.SyncError, "Missing packaged reference"):
            s.validate_files({"diagram.svg": svg}, [])

    def test_generated_allowlist_is_reserved(self):
        self.c["assets"][0]["members"][0]["destination"] = "publication-allowlist.json"
        self.save()
        with self.assertRaisesRegex(s.SyncError, "reserved generated allowlist"):
            self.prepare()

    def test_concurrent_late_receipt_cannot_regress_state(self):
        old_run = self.prepare()
        self.approve(old_run)
        old_m = s.read_json(old_run / "manifest.json")
        old_readback = self.root / "old-readback.json"
        s.write_json(old_readback, {"repository": "example/kit", "branch": "main", "parent": "a" * 40,
            "commit": "d" * 40, "head_after": "d" * 40, "tree_sha": "e" * 40, "files": old_m["expected_tree"]})
        s.receipt(old_run, old_readback)
        self.b.update(commit="d" * 40, tree_sha="e" * 40, files=old_m["expected_tree"])
        s.write_json(self.bp, self.b)
        (self.root / "content" / "guide.md").write_text("# Updated guide\n", encoding="utf-8")
        new_run = self.prepare()
        self.approve(new_run)
        new_m = s.read_json(new_run / "manifest.json")
        new_readback = self.root / "new-readback.json"
        s.write_json(new_readback, {"repository": "example/kit", "branch": "main", "parent": "d" * 40,
            "commit": "f" * 40, "head_after": "f" * 40, "tree_sha": "1" * 40, "files": new_m["expected_tree"]})
        entered, release = threading.Event(), threading.Event()
        original_read = s.read_json
        results = []

        def blocked_read(path):
            value = original_read(path)
            if Path(path) == self.root / "state.json" and threading.current_thread().name == "new-receipt":
                entered.set()
                if not release.wait(10):
                    raise RuntimeError("Test synchronization timed out")
            return value

        def finish_new():
            results.append(s.receipt(new_run, new_readback))

        with patch.object(s, "read_json", side_effect=blocked_read):
            thread = threading.Thread(target=finish_new, name="new-receipt")
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaisesRegex(s.SyncError, "locked"):
                    s.receipt(old_run, old_readback)
            finally:
                release.set()
                thread.join(10)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["state_advanced"])
        self.assertFalse(s.receipt(old_run, old_readback)["state_advanced"])
        self.assertEqual(s.read_json(self.root / "state.json")["commit"], "f" * 40)

    def test_inventory_discovers_only_declared_roots_without_approving(self):
        skills = self.root / "skills"
        (skills / "new-skill").mkdir(parents=True)
        (skills / "new-skill" / "SKILL.md").write_text("# Synthetic skill", encoding="utf-8")
        self.c["inventory_roots"] = [{"id": "local", "kind": "skill-directories", "path": "skills"}]
        self.save()
        before = self.cp.read_bytes()
        r = s.inventory(self.cp)
        self.assertEqual(r["entry_count"], 1)
        self.assertEqual(r["changed"], ["local/new-skill"])
        self.assertFalse(r["publication_approval_changed"])
        self.assertFalse((self.root / "state/inventory.json").exists())
        self.assertEqual(self.cp.read_bytes(), before)

    def test_inventory_repeat_does_not_rewrite_unchanged_state(self):
        self.c["inventory_roots"] = [{"id": "docs", "kind": "files", "path": "content", "include": ["guide.md"]}]
        self.save()
        self.assertTrue(s.inventory(self.cp, record=True)["recorded"])
        state = self.root / "state/inventory.json"
        before = state.stat().st_mtime_ns
        r = s.inventory(self.cp, record=True)
        self.assertFalse(r["recorded"])
        self.assertEqual(r["changed"], [])
        self.assertEqual(state.stat().st_mtime_ns, before)

    def test_missing_inventory_root_never_records_deletion(self):
        self.c["inventory_roots"] = [{"id": "missing", "kind": "files", "path": "absent", "include": ["guide.md"]}]
        self.save()
        r = s.inventory(self.cp, record=True)
        self.assertTrue(r["blocked"])
        self.assertFalse(r["recorded"])
        self.assertEqual(r["removed_candidates"], [])

    def test_state_cannot_silently_move_to_another_branch(self):
        s.write_json(self.root / "state.json", {"repository": "example/kit", "branch": "another", "managed_files": {}})
        with self.assertRaisesRegex(s.SyncError, "another branch"):
            self.prepare()

    def test_target_privacy_policy_is_scoped_and_requires_new_digest(self):
        (self.root / "content" / "guide.md").write_text("TARGET_PRIVATE_EXAMPLE", encoding="utf-8")
        self.c["targets"]["kit"]["private_patterns"] = ["TARGET_PRIVATE_EXAMPLE"]
        s.write_json(self.cp, self.c)
        with self.assertRaisesRegex(s.SyncError, "Target scope changed"):
            self.prepare()
        self.save()
        with self.assertRaisesRegex(s.SyncError, "Private/secret"):
            self.prepare()


if __name__ == "__main__":
    unittest.main(verbosity=2)
