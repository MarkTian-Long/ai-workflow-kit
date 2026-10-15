#!/usr/bin/env python3
"""Prepare reviewed, allowlisted GitHub snapshots. Standard library; no network."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from urllib.parse import unquote, urlsplit
import uuid
import xml.etree.ElementTree as ET


class SyncError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_bytes(json.dumps(value, ensure_ascii=False, indent=2).encode() + b"\n")
    os.replace(temp, path)


def relpath(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise SyncError(f"Invalid relative path: {value!r}")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x.casefold() in {"..", ".git"} for x in p.parts):
        raise SyncError(f"Path escapes its scope: {value}")
    if value != p.as_posix() or p.as_posix() == ".":
        raise SyncError(f"Path must be normalized: {value}")
    return value


def safe_file(root, relative):
    root = Path(root).absolute()
    relative = relpath(relative)
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise SyncError(f"Source escapes root: {relative}")
    for part in [path, *path.parents]:
        if part.exists():
            s = part.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
                raise SyncError(f"Linked/reparse source refused: {part}")
        if part == root:
            break
    if not path.is_file():
        raise SyncError(f"Source file missing: {path}; missing is never a deletion")
    return path


def asset_policy(asset):
    return digest(canonical({k: v for k, v in asset.items() if k not in {
        "approved_policy_sha256", "authorization_note", "status", "last_receipt"
    }}))


def target_policy(target):
    return digest(canonical({k: v for k, v in target.items() if k not in {
        "approved_policy_sha256", "authorization_note"
    }}))


def config(path):
    path = Path(path).resolve()
    c = read_json(path)
    if c.get("schema_version") != 1:
        raise SyncError("Unsupported catalog schema; migrate explicitly")
    ids = [a["id"] for a in c["assets"]]
    if len(ids) != len(set(ids)):
        raise SyncError("Duplicate asset id")
    return path, c


def local_path(catalog_path, value):
    p = Path(value)
    return p if p.is_absolute() else catalog_path.parent / p


def adapt(data, transformations):
    if not transformations:
        return data
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    for rule in transformations:
        op = rule["op"]
        if op == "replace":
            n = text.count(rule["old"])
            if n != rule.get("count", 1):
                raise SyncError(f"Adapter drift: expected {rule.get('count', 1)}, got {n}")
            text = text.replace(rule["old"], rule["new"])
        elif op == "regex":
            text, n = re.subn(rule["pattern"], rule["replacement"], text, flags=re.MULTILINE)
            if n != rule.get("count", 1):
                raise SyncError(f"Regex adapter drift: {n} matches")
        elif op == "section":
            if text.count(rule["start"]) != 1 or text.count(rule["end"]) != 1:
                raise SyncError("Section adapter drift")
            left = text.index(rule["start"])
            right = text.index(rule["end"], left)
            text = text[:left] + rule["replacement"] + text[right:]
        elif op == "trim_after":
            if text.count(rule["marker"]) != 1:
                raise SyncError("Footer adapter drift")
            text = text.split(rule["marker"])[0].rstrip() + "\n" + rule.get("replacement", "")
        else:
            raise SyncError(f"Unknown adapter: {op}")
    return text.encode("utf-8")


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value and name.rsplit(":", 1)[-1] in {"src", "href", "poster", "data", "action"}:
                self.links.append((value, tag not in {"a"}))


def validate_files(files, private_patterns):
    links = 0
    folded = set()
    for name, data in files.items():
        relpath(name)
        if name.casefold() in folded:
            raise SyncError(f"Case-colliding target: {name}")
        folded.add(name.casefold())
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SyncError(f"Only explicitly reviewed UTF-8 assets supported: {name}") from exc
        for pattern in private_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                raise SyncError(f"Private/secret marker in {name} (pattern {private_patterns.index(pattern)})")
        refs = []
        suffix = Path(name).suffix.lower()
        if suffix == ".md":
            refs = [(a or b, False) for a, b in re.findall(r"\[[^\]\n]+\]\((?:<([^>]+)>|([^\)\n]+))\)", text)]
        elif suffix in {".html", ".htm", ".svg"}:
            p = Resources()
            p.feed(text)
            refs = p.links
            if suffix == ".svg":
                ET.fromstring(text)
        if suffix in {".html", ".htm", ".svg", ".css"}:
            refs.extend((x, True) for x in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", text))
            if re.search(r"@import|(?:https?:)?//[^\s'\"]+", text) and suffix == ".css":
                raise SyncError(f"External CSS resource needs explicit review: {name}")
        for value, resource in refs:
            u = urlsplit(value)
            if not value or value.startswith("#"):
                continue
            if u.scheme or u.netloc:
                if resource and u.scheme != "data":
                    raise SyncError(f"External runtime resource in {name}: {value}")
                continue
            target = (PurePosixPath(name).parent / unquote(u.path)).as_posix()
            normalized = os.path.normpath(target).replace("\\", "/")
            if normalized not in files:
                raise SyncError(f"Missing packaged reference: {name} -> {value}")
            links += 1
    return {"utf8_files": len(files), "local_references": links, "privacy_scan": "passed",
            "semantic_review": "required separately; static checks do not establish rights or behavior"}


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SyncError(f"Target preparation already locked: {path}; inspect owner before removing") from exc
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def prepare(catalog_path, target_id, baseline_path):
    cp, c = config(catalog_path)
    target = c["targets"][target_id]
    if not target.get("enabled") or target.get("mode") != "reviewed-snapshot":
        raise SyncError("Target is not enabled for reviewed snapshots")
    if not target.get("authorization_note") or target.get("approved_policy_sha256") != target_policy(target):
        raise SyncError("Target scope changed; review repository, visibility and publishing policy")
    baseline = read_json(baseline_path)
    if (baseline.get("repository"), baseline.get("branch")) != (target["repository"], target["branch"]):
        raise SyncError("Baseline destination mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", baseline.get("commit", "")):
        raise SyncError("A frozen remote commit is required")
    state_path = local_path(cp, target["state_path"])
    state = read_json(state_path) if state_path.exists() else {"managed_files": {}}
    if state.get("repository", target["repository"]) != target["repository"]:
        raise SyncError("Previous receipt belongs to another repository")
    if state.get("branch", target["branch"]) != target["branch"]:
        raise SyncError("Previous receipt belongs to another branch; migrate state explicitly")
    runs = local_path(cp, c["runs_root"])
    with locked(runs / (target_id + ".lock")):
        files, sources, frozen_sources, policies, owners = {}, [], [], {}, {}
        for asset in c["assets"]:
            if asset.get("target") != target_id or asset.get("status") != "approved":
                continue
            if not asset.get("license") or not asset.get("authorization_note"):
                raise SyncError(f"Rights/authorization absent: {asset['id']}")
            if asset.get("approved_policy_sha256") != asset_policy(asset):
                raise SyncError(f"Asset boundary changed; review policy: {asset['id']}")
            policies[asset["id"]] = asset_policy(asset)
            source_root = local_path(cp, asset["source_root"])
            for member in asset["members"]:
                path = safe_file(source_root, member["source"])
                data = path.read_bytes()
                dest = relpath(member["destination"])
                if dest in files:
                    raise SyncError(f"Duplicate target: {dest}")
                sources.append({"path": str(path), "source_root": str(source_root),
                    "relative": member["source"], "sha256": digest(data), "snapshot": str(len(sources))})
                frozen_sources.append(data)
                files[dest] = adapt(data, member.get("transforms", []))
                owners[dest] = asset["id"]
        if not files:
            raise SyncError("No approved assets for target")
        allow_path = relpath(target["allowlist_path"])
        allow_mode = target.get("allowlist_mode", "generated")
        if allow_mode == "generated":
            if allow_path in files:
                raise SyncError(f"Asset conflicts with reserved generated allowlist: {allow_path}")
            files[allow_path] = json.dumps({"schema_version": 1, "license": target["license"],
                "source_policy": "generated reviewed snapshots; authoritative sources maintained separately",
                "files": sorted([*files, allow_path])}, ensure_ascii=False, indent=2).encode() + b"\n"
            owners[allow_path] = "generated-allowlist"
        elif allow_mode == "source-sha256-manifest":
            if allow_path not in files:
                raise SyncError("Source manifest missing from approved assets")
            try:
                declared = json.loads(files[allow_path])["files"]
            except (ValueError, KeyError, TypeError) as exc:
                raise SyncError("Invalid source SHA-256 manifest") from exc
            expected_manifest = {p: {"bytes": len(data), "sha256": digest(data)}
                                 for p, data in files.items() if p != allow_path}
            if declared != expected_manifest:
                raise SyncError("Source manifest does not cover exact prepared bytes/members")
        else:
            raise SyncError(f"Unknown allowlist mode: {allow_mode}")
        checks = validate_files(files, target.get("private_patterns", c["private_patterns"]))
        removals = target.get("removals", [])
        removed = {relpath(x["path"]) for x in removals if x.get("approved") and x.get("reason")}
        if removed.intersection(files):
            raise SyncError("A target cannot be published and removed simultaneously")
        orphaned = set(state["managed_files"]) - set(files) - removed
        if orphaned:
            raise SyncError(f"Previously managed paths require explicit retirement: {sorted(orphaned)}")
        remote = baseline["files"]
        unowned = [p for p in files if p in remote and p not in state["managed_files"]
            and remote[p] != blob(files[p]) and target.get("adopt_existing", {}).get(p) != remote[p]]
        if unowned:
            raise SyncError(f"Existing unmanaged paths require explicit baseline adoption: {unowned}")
        conflicts = [p for p, old in state["managed_files"].items()
            if remote.get(p) != old and remote.get(p) != (blob(files[p]) if p in files else None)]
        if conflicts:
            raise SyncError(f"Remote owned files changed; merge before publishing: {conflicts}")
        changed = {p: data for p, data in files.items() if remote.get(p) != blob(data)}
        deletions = sorted(p for p in removed if p in remote)
        expected = {**remote, **{p: blob(data) for p, data in files.items()}}
        for p in deletions:
            del expected[p]
        run = runs / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
        run.mkdir(parents=True)
        (run / "source-snapshot").mkdir()
        for i, data in enumerate(frozen_sources):
            (run / "source-snapshot" / str(i)).write_bytes(data)
        for name, data in files.items():
            path = run / "files" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        manifest = {"schema_version": 1, "target": target_id, "repository": target["repository"],
            "branch": target["branch"], "catalog": str(cp), "catalog_sha256": digest(cp.read_bytes()),
            "source_files": sources, "asset_policies": policies, "baseline_commit": baseline["commit"],
            "baseline_tree": baseline["tree_sha"], "checks": checks, "state_path": str(state_path),
            "files": {p: {"sha256": digest(data), "git_blob": blob(data), "owner": owners[p]} for p, data in files.items()},
            "changed": sorted(changed), "deletions": deletions, "expected_tree": expected,
            "status": "no-change" if not changed and not deletions else "awaiting-review"}
        write_json(run / "manifest.json", manifest)
        return {"run": str(run), "status": manifest["status"], "changed": len(changed),
                "deletions": len(deletions), "files": len(files), "checks": checks}


def verify_run(run, current=True):
    run = Path(run).resolve()
    m = read_json(run / "manifest.json")
    cp = Path(m["catalog"])
    if current and digest(cp.read_bytes()) != m["catalog_sha256"]:
        raise SyncError("Catalog changed after preparation; prepare a new run")
    for source in m["source_files"]:
        if digest((run / "source-snapshot" / source["snapshot"]).read_bytes()) != source["sha256"]:
            raise SyncError("Frozen source snapshot changed")
        if current:
            p = safe_file(source["source_root"], source["relative"])
            if digest(p.read_bytes()) != source["sha256"]:
                raise SyncError(f"Source changed after preparation: {p}")
    for path, meta in m["files"].items():
        p = safe_file(run / "files", path)
        if digest(p.read_bytes()) != meta["sha256"]:
            raise SyncError(f"Prepared payload changed: {path}")
    return m


def review(run, note, checks):
    m = verify_run(run)
    if m["status"] == "no-change":
        raise SyncError("No-change runs must not create commits")
    if not note.strip() or not checks:
        raise SyncError("Record actual semantic/rights and type-specific checks")
    write_json(Path(run) / "review.json", {"manifest_sha256": digest((Path(run) / "manifest.json").read_bytes()),
        "decision": "approved", "note": note, "checks": checks})
    return {"review": "recorded", "run": str(run)}


def upload_plan(run):
    run = Path(run)
    m = verify_run(run)
    r = read_json(run / "review.json")
    if r.get("decision") != "approved" or r["manifest_sha256"] != digest((run / "manifest.json").read_bytes()):
        raise SyncError("Review does not cover this exact prepared set")
    if m["status"] == "no-change":
        raise SyncError("No changes to publish")
    plan = {"repository": m["repository"], "branch": m["branch"], "expected_sha": m["baseline_commit"],
        "base_tree_sha": m["baseline_tree"], "force": False,
        "files": [{"path": p, "encoding": "base64", "content": base64.b64encode((run / "files" / p).read_bytes()).decode(),
                   "git_blob": m["files"][p]["git_blob"]} for p in m["changed"]], "deletions": m["deletions"]}
    write_json(run / "upload-plan.json", plan)
    return {"plan": str(run / "upload-plan.json"), "changed": len(plan["files"]),
            "expected_sha": plan["expected_sha"], "network": "not performed"}


def receipt(run, readback_path):
    run = Path(run)
    m = verify_run(run, current=False)
    r = read_json(run / "review.json")
    if r.get("decision") != "approved" or r.get("manifest_sha256") != digest((run / "manifest.json").read_bytes()):
        raise SyncError("Readback has no matching approved review")
    result = read_json(readback_path)
    if (result.get("repository"), result.get("branch")) != (m["repository"], m["branch"]):
        raise SyncError("Readback destination mismatch")
    if result.get("parent") != m["baseline_commit"] or result.get("head_after") != result.get("commit"):
        raise SyncError("Readback is not the expected non-force update")
    if result.get("files") != m["expected_tree"]:
        raise SyncError("Remote readback does not match the complete expected tree")
    state = {"schema_version": 1, "repository": m["repository"], "branch": m["branch"],
        "commit": result["commit"], "tree_sha": result["tree_sha"],
        "managed_files": {p: v["git_blob"] for p, v in m["files"].items()}, "receipt": str(run / "receipt.json")}
    state_path = Path(m["state_path"])
    with locked(state_path.with_name(state_path.name + ".lock")):
        current_state = read_json(state_path) if state_path.exists() else {}
        advance = current_state.get("commit") in {None, m["baseline_commit"], result["commit"]}
        write_json(run / "receipt.json", {**state, "readback": "complete Git tree/blob identity match",
            "source_adoption": "not asserted", "state_advanced": advance, "review": r})
        if advance:
            write_json(state_path, state)
    return {"published": True, "commit": state["commit"], "receipt": state["receipt"], "state_advanced": advance}


def inventory(catalog_path, record=False):
    """Discover metadata only within declared roots; never change publication approval."""
    cp, c = config(catalog_path)
    roots = c.get("inventory_roots", [])
    if len({r["id"] for r in roots}) != len(roots):
        raise SyncError("Duplicate inventory root id")
    state_path = local_path(cp, c.get("inventory_state", "state/inventory.json"))

    def scan():
        entries, blocked = {}, []
        for root in roots:
            base = local_path(cp, root["path"])
            if not base.is_dir():
                blocked.append({"root": root["id"], "reason": "declared root missing"})
                continue
            if root["kind"] == "skill-directories":
                candidates = [(p.name, [p.name + "/" + f for f in root.get("evidence_files", ["SKILL.md"])
                    if (p / f).is_file()]) for p in sorted(base.iterdir())
                    if p.is_dir() and (p / "SKILL.md").is_file()]
            elif root["kind"] == "files":
                candidates = [(p, [p]) for p in root["include"]]
            else:
                raise SyncError(f"Unknown inventory root kind: {root['kind']}")
            for name, paths in candidates:
                key = root["id"] + "/" + name
                try:
                    hashes = {p: digest(safe_file(base, p).read_bytes()) for p in paths}
                    entries[key] = {"root": root["id"], "source": str(base / name),
                        "signature": digest(canonical(hashes)), "members": hashes,
                        "disposition": "discovered; approval comes only from the asset catalog"}
                except (SyncError, OSError) as exc:
                    blocked.append({"root": root["id"], "entry": key, "reason": str(exc)})
        previous = read_json(state_path) if state_path.exists() else {"entries": {}}
        old = previous.get("entries", {})
        changed = sorted(k for k, v in entries.items() if old.get(k, {}).get("signature") != v["signature"])
        removed = sorted(set(old) - set(entries)) if not blocked else []
        root_signature = digest(canonical(roots))
        scope_changed = previous.get("root_signature") != root_signature
        saved = False
        if record and not blocked and (changed or removed or scope_changed):
            write_json(state_path, {"schema_version": 1, "root_signature": root_signature, "entries": entries})
            saved = True
        return {"entry_count": len(entries), "roots": len(roots), "changed": changed,
            "removed_candidates": removed, "scope_changed": scope_changed, "blocked": blocked,
            "recorded": saved, "entries": entries, "publication_approval_changed": False}

    if record:
        with locked(state_path.with_name(state_path.name + ".lock")):
            return scan()
    return scan()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("prepare")
    s.add_argument("--catalog", required=True)
    s.add_argument("--target", required=True)
    s.add_argument("--baseline", required=True)
    for command in ["review", "upload-plan", "receipt"]:
        s = sub.add_parser(command)
        s.add_argument("--run", required=True)
        if command == "review":
            s.add_argument("--note", required=True)
            s.add_argument("--check", action="append", required=True)
        elif command == "receipt":
            s.add_argument("--readback", required=True)
    s = sub.add_parser("policy-digests")
    s.add_argument("--catalog", required=True)
    s = sub.add_parser("inventory")
    s.add_argument("--catalog", required=True)
    s.add_argument("--record", action="store_true", help="Record a changed complete inventory locally; never approve publication")
    args = p.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.catalog, args.target, args.baseline)
        elif args.command == "review":
            result = review(args.run, args.note, args.check)
        elif args.command == "upload-plan":
            result = upload_plan(args.run)
        elif args.command == "receipt":
            result = receipt(args.run, args.readback)
        elif args.command == "inventory":
            result = inventory(args.catalog, args.record)
        else:
            _, c = config(args.catalog)
            result = {"assets": {a["id"]: asset_policy(a) for a in c["assets"]},
                      "targets": {k: target_policy(v) for k, v in c["targets"].items() if v.get("enabled")}}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (SyncError, OSError, ValueError, KeyError, ET.ParseError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
