# Copyright 2026 Google LLC.
# SPDX-License-Identifier: Apache-2.0

"""Offline Copilot package contracts; no model or isolation claims."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading

import pytest

from .test_harnesses import REVIEWERS, frontmatter


def test_copilot_profiles_use_canonical_read_only_reviewers(repo_root: Path) -> None:
    profiles = repo_root / "com.github.copilot/agents"
    expected_names = {
        frontmatter(repo_root / f"agents/{p}.md")["name"] for p in REVIEWERS
    }
    assert {p.stem.removesuffix(".agent") for p in profiles.glob("*.agent.md")} == (
        expected_names | {"egm"}
    )
    for persona in REVIEWERS:
        canonical = repo_root / f"agents/{persona}.md"
        name = frontmatter(canonical)["name"]
        profile = profiles / f"{name}.agent.md"
        config = frontmatter(profile)
        assert config["name"] == name
        assert config["tools"] == ["read", "search"]
        assert config["include-custom-instructions"] is False
        assert config["user-invocable"] is False
        assert set(config) == {
            "name", "description", "tools", "include-custom-instructions",
            "user-invocable",
        }
        text = profile.read_text(encoding="utf-8")
        assert f"<EGM_ROOT>/agents/{persona}.md" in text
        assert "incomplete review" in text
        assert "Do not retrieve parent history" in text
        assert "${" not in text  # No undocumented Markdown variable expansion.
    entry = profiles / "egm.agent.md"
    assert frontmatter(entry)["tools"] == ["read", "search", "edit", "agent"]
    assert "<EGM_ROOT>/docs/copilot.md" in entry.read_text(encoding="utf-8")


@pytest.mark.parametrize("persona", [*REVIEWERS, None])
def test_copilot_prior_reports_require_explicit_stage_input(
    repo_root: Path, persona: str | None,
) -> None:
    """Stage 8 may read its prior report without opening parent context."""
    path = repo_root / "docs/copilot.md"
    if persona is not None:
        name = frontmatter(repo_root / f"agents/{persona}.md")["name"]
        path = repo_root / f"com.github.copilot/agents/{name}.agent.md"
    text = " ".join(path.read_text(encoding="utf-8").split())
    assert "Do not retrieve parent history or memory." in text
    assert (
        "Read prior reviewer reports only when explicitly supplied in the reading "
        "list and required by the canonical workflow stage."
    ) in text


@pytest.fixture
def copilot_package(repo_root: Path, tmp_path: Path) -> Path:
    """Relocate the full runtime, including paths with spaces and Unicode."""
    package = tmp_path / "relocated EGM café"
    package.mkdir()
    for directory in ("skills", "agents", "resources", "docs", "com.github.copilot", ".plugin"):
        shutil.copytree(repo_root / directory, package / directory)
    shutil.copy2(repo_root / "plugin.json", package / "plugin.json")
    return package


def test_copilot_relocated_resources(repo_root: Path, copilot_package: Path) -> None:
    for directory in ("skills", "agents", "resources", "docs"):
        for source in (repo_root / directory).rglob("*"):
            if source.is_file():
                installed = copilot_package / source.relative_to(repo_root)
                assert installed.read_bytes() == source.read_bytes()
    for skill in (copilot_package / "skills").glob("*/SKILL.md"):
        assert skill.parents[2] == copilot_package
    profiles = copilot_package / "com.github.copilot/agents"
    for profile in profiles.glob("*.agent.md"):
        text = profile.read_text(encoding="utf-8")
        for relative in re.findall(r"<EGM_ROOT>/([\w/.-]+)", text):
            assert (copilot_package / relative).exists(), (profile.name, relative)
    assert not (copilot_package / "com.github.copilot/skills").exists()


def test_copilot_native_offline_discovery(
    copilot_package: Path, tmp_path: Path,
) -> None:
    """Inspect the native session loader without sending a model prompt."""
    if os.environ.get("EGM_COPILOT_OFFLINE") != "1":
        pytest.skip("Set EGM_COPILOT_OFFLINE=1 for native loader inspection")
    executable = shutil.which("copilot")
    if executable is None:
        pytest.skip("Copilot CLI is not installed")
    version = subprocess.check_output([executable, "--version"], text=True)
    assert "GitHub Copilot CLI 1.0.82." in version
    provider_requests = []

    class RejectProvider(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            provider_requests.append(self.path)
            self.send_error(503)

        do_GET = do_POST

        def log_message(self, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), RejectProvider) as provider:
        threading.Thread(target=provider.serve_forever, daemon=True).start()
        env = {k: v for k, v in os.environ.items() if not any(
            token in k for token in ("TOKEN", "API_KEY", "BEARER", "COPILOT_")
        )}
        base_url = f"http://127.0.0.1:{provider.server_port}/v1"
        env.update(COPILOT_OFFLINE="true", COPILOT_HOME=str(tmp_path / "profile"),
                   COPILOT_PROVIDER_BASE_URL=base_url, COPILOT_MODEL="gpt-4.1")
        responses: queue.Queue = queue.Queue()
        with (tmp_path / "loader.log").open("w") as log:
            process = subprocess.Popen(
                [executable, "--plugin-dir", str(copilot_package), "--headless",
                 "--stdio", "--no-auto-update", "--no-auto-login",
                 "--disable-builtin-mcps"],
                cwd=tmp_path, env=env, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=log,
            )

            def receive() -> None:
                try:
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            raise EOFError("Copilot loader closed stdout")
                        if line.lower().startswith(b"content-length:"):
                            length = int(line.split(b":")[1])
                            while process.stdout.readline().strip():
                                pass
                            responses.put(json.loads(process.stdout.read(length)))
                except Exception as error:
                    responses.put(error)

            threading.Thread(target=receive, daemon=True).start()
            request_id = 0

            def rpc(method: str, params: dict) -> dict:
                nonlocal request_id
                request_id += 1
                body = json.dumps({"jsonrpc": "2.0", "id": request_id,
                                   "method": method, "params": params}).encode()
                header = f"Content-Length: {len(body)}\r\n\r\n".encode()
                process.stdin.write(header + body)
                process.stdin.flush()
                while True:
                    response = responses.get(timeout=20)
                    if isinstance(response, Exception):
                        raise response
                    if response.get("id") == request_id:
                        assert "error" not in response, response
                        return response["result"]

            try:
                session = rpc("session.create", {
                    "model": "gpt-4.1", "workingDirectory": str(tmp_path),
                    "provider": {"type": "openai", "baseUrl": base_url},
                })
                params = {"sessionId": session["sessionId"]}
                agents = rpc("session.agent.list", params)["agents"]
                profiles = copilot_package / "com.github.copilot/agents"
                expected = {f"egm:{frontmatter(p)['name']}": p
                            for p in profiles.glob("*.agent.md")}
                loaded = {a["id"]: a for a in agents if a["source"] == "plugin"}
                assert set(loaded) == set(expected)
                for name, path in expected.items():
                    config = frontmatter(path)
                    assert Path(loaded[name]["path"]) == path
                    assert loaded[name]["tools"] == config["tools"]
                    assert loaded[name]["userInvocable"] == config.get(
                        "user-invocable", True
                    )
                    assert loaded[name]["mcpServers"] == {}
                skills = rpc("session.skills.list", params)["skills"]
                loaded_skills = {s["commandName"]: s for s in skills
                                 if s["source"] == "plugin"}
                expected_skills = {f"egm:{frontmatter(p)['name']}": p
                                   for p in (copilot_package / "skills").glob("*/SKILL.md")}
                assert set(loaded_skills) == set(expected_skills)
                for name, path in expected_skills.items():
                    assert Path(loaded_skills[name]["path"]) == path
                    assert loaded_skills[name]["enabled"] is True
                rpc("session.destroy", params)
            finally:
                process.terminate()
                process.wait(timeout=5)
                process.stdin.close()
                process.stdout.close()
                provider.shutdown()
                assert provider_requests == [], "Loader attempted model access"
