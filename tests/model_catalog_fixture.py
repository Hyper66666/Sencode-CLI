"""Enabled model projection using only a fresh temporary catalog and no secrets."""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
from tui_console_fixture import environment_for


def cleanup(root: Path) -> None:
    root = root.resolve()
    paths = list(root.rglob("*"))
    assert all(path.resolve().is_relative_to(root) for path in paths)
    for path in paths:
        if path.is_file() or path.is_symlink():
            path.unlink()
    for path in sorted((p for p in paths if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        path.rmdir()
    root.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--public", action="store_true", help="Exercise the installed public models command")
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    root = Path(tempfile.mkdtemp(prefix="sencode-model-catalog-中文-")).resolve()
    database = root / "isolated.sqlite3"
    checks = []
    environment = environment_for(root)

    def read():
        command = [str(executable), "models", "--database", str(database), "--cwd", str(root)] if args.public else [str(executable), str(database)]
        result = subprocess.run(command, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=30)
        assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
        return json.loads(result.stdout)

    try:
        assert read()["connections"] == []
        checks.append("empty-isolated-catalog")
        enabled = [{"id": f"model-{n}", "label": f"模型 {n} 😀", "capabilities": {"visionSupported": n == 7,
                    "reasoningEffort": n != 3, "customCapability": {"preserved": True}}} for n in range(37)]
        configs = [
            ("first", "customApi", "渠道甲", {"baseUrl": "https://example.invalid/v1", "protocol": "responses", "selectedModelId": "model-0", "enabledModels": enabled, "discoveredModelIds": ["not-enabled"]}, "model-0"),
            ("second", "customApi", "渠道乙", {"baseUrl": "https://example.invalid/v1", "protocol": "messages", "selectedModelId": "model-0", "enabledModels": [{"id": "model-0", "label": "Second source", "capabilities": {"visionSupported": False}}]}, "model-0"),
            ("denied", "customApi", "Effort denied", {"baseUrl": "https://example.invalid/v1", "protocol": "chatCompletions", "selectedModelId": "model", "capabilities": {"reasoningEffort": False}, "enabledModels": [{"id": "model", "capabilities": {"visionSupported": False}}]}, "model"),
            ("legacy", "customApi", "Legacy", {"baseUrl": "https://example.invalid/v1", "protocol": "chatCompletions", "selectedModelId": "old", "enabledModels": []}, "old"),
            ("official", "codex", "Account", {}, "account-default"),
        ]
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "isolated-model-catalog" if key == "instance_id" else None)
            for index, (identifier, kind, name, config, selected) in enumerate(configs):
                db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES(?,?,'managed',?,?,?,?,?)",
                           (identifier, kind, name, json.dumps(config, ensure_ascii=False), selected, index + 1, index + 1))
            db.commit()
        catalog = read()
        channels = catalog["connections"]
        assert [c["id"] for c in channels] == [c[0] for c in configs]
        checks.append("all-suppliers-preserve-stable-order-without-default-supplier-filtering")
        assert len(channels[0]["models"]) == 37
        assert [m["id"] for m in channels[0]["models"]] == [m["id"] for m in enabled]
        assert "not-enabled" not in json.dumps(channels[0]["models"])
        checks.append("all-37-enabled-models-retained-discovery-only-excluded")
        assert channels[0]["models"][7]["capabilities"] == enabled[7]["capabilities"]
        assert channels[0]["models"][7]["label"] == "模型 7 😀"
        checks.append("complete-desktop-model-capability-and-unicode-label-roundtrip")
        assert channels[0]["models"][0]["efforts"] == ["low", "medium", "high", "xhigh", "max"]
        assert channels[0]["models"][3]["efforts"] == []
        assert channels[1]["models"][0]["efforts"] == ["low", "medium", "high", "xhigh", "max"]
        assert channels[2]["models"][0]["efforts"] == []
        checks.append("native-protocol-effort-contract-with-explicit-model-and-connection-denials")
        assert channels[1]["models"][0]["id"] == channels[0]["models"][0]["id"]
        assert channels[1]["models"][0]["label"] == "Second source"
        checks.append("same-model-id-keeps-independent-connection-projection")
        assert channels[3]["models"][0]["id"] == "old"
        checks.append("legacy-selected-model-compatibility")
        assert channels[4]["models"][0]["efforts"] == []
        checks.append("account-name-never-grants-unsupported-effort")
        with closing(sqlite3.connect(database)) as db:
            db.create_function("sengoo_context", 1, lambda key: "isolated-model-catalog" if key == "instance_id" else None)
            db.execute("INSERT INTO connection_configs(id,kind,profile_scope,display_name,config_json,selected_model_id,created_at,updated_at) VALUES('new-supplier','customApi','managed','New supplier',?,'fresh',10,10)",
                       (json.dumps({"baseUrl": "https://example.invalid/v1", "protocol": "responses", "enabledModels": [{"id": "fresh"}, {"id": "shared"}]}),))
            db.commit()
        refreshed = read()["connections"]
        assert len(refreshed) == 6 and refreshed[-1]["id"] == "new-supplier", refreshed
        assert [m["id"] for m in refreshed[-1]["models"]] == ["fresh", "shared"]
        checks.append("catalog-reopen-refreshes-additional-supplier-and-enabled-models")
        evidence = {"schema": 1, "result": "passed", "scope": "isolated-native-model-catalog", "checks": checks,
                    "binary_sha256": hashlib.sha256(executable.read_bytes()).hexdigest()}
        print(json.dumps(evidence, ensure_ascii=False))
        if args.evidence:
            args.evidence.resolve().write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    finally:
        cleanup(root)


if __name__ == "__main__":
    main()
