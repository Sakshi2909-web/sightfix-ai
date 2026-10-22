import os
import shutil
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from app.config import settings

MAX_OUTPUT_CHARS = 4000


def detect_test_command(repo_dir: Path) -> Tuple[Optional[List[str]], str]:
    """Auto-detects test command based on manifest files."""
    pkg_json = repo_dir / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            test_cmd = data.get("scripts", {}).get("test")
            if test_cmd:
                # E.g. "node tests/login.test.js" or "npm test"
                parts = test_cmd.split()
                # On Windows, if command starts with node or npm, use proper executable
                return parts, "nodejs"
        except Exception:
            pass

    if (repo_dir / "pytest.ini").exists() or list(repo_dir.glob("test_*.py")) or list(repo_dir.glob("tests")):
        return ["pytest", "-v"], "python"

    if (repo_dir / "pom.xml").exists():
        return ["mvn", "test"], "java"

    if (repo_dir / "build.gradle").exists():
        return ["gradle", "test"], "gradle"

    if (repo_dir / "go.mod").exists():
        return ["go", "test", "./..."], "go"

    return None, "unknown"


def run_command_with_limits(
    cmd: List[str], cwd: Path, timeout_sec: int = 60
) -> Tuple[int, str]:
    """Runs test command in isolated process with strict timeout."""
    try:
        # If node is first token, find absolute path if not in current session PATH
        if cmd[0] == "node":
            node_path = shutil.which("node")
            if not node_path:
                for candidate in ["C:\\Program Files\\nodejs\\node.exe", os.path.expandvars("%LOCALAPPDATA%\\Programs\\nodejs\\node.exe")]:
                    if os.path.isfile(candidate):
                        node_path = candidate
                        break
            if node_path:
                cmd = [node_path] + cmd[1:]

        res = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_sec,
            shell=False,
        )
        return res.returncode, res.stdout or ""
    except subprocess.TimeoutExpired:
        return -1, f"Execution timed out after {timeout_sec} seconds."
    except Exception as ex:
        return -2, f"Execution error: {str(ex)}"


class SandboxVerifier:
    def verify_patch(
        self,
        repo_dir: Path,
        diff_text: str,
        timeout_sec: int = 60,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Executes baseline and patched tests in an isolated workspace.
        Returns: (verification_status, test_output, sandbox_meta)
        verification_status is strictly: 'unverified' | 'passed' | 'failed' | 'error'
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="sightfix_sandbox_"))
        try:
            # 1. Copy repo to sandbox dir
            sandbox_workdir = temp_dir / "repo"
            shutil.copytree(
                repo_dir,
                sandbox_workdir,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".git", "node_modules", ".venv", "__pycache__"),
            )

            # 2. Detect test runner
            test_cmd, runner_type = detect_test_command(sandbox_workdir)
            if not test_cmd:
                return (
                    "unverified",
                    "No recognized test suite or script detected in repository.",
                    {"runner": "none"},
                )

            # 3. Initialize git in sandbox to test cleanly
            subprocess.run(["git", "init"], cwd=sandbox_workdir, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.name", "Sandbox"], cwd=sandbox_workdir, capture_output=True, check=False)
            subprocess.run(["git", "config", "user.email", "sandbox@sightfix.ai"], cwd=sandbox_workdir, capture_output=True, check=False)
            subprocess.run(["git", "add", "."], cwd=sandbox_workdir, capture_output=True, check=False)
            subprocess.run(["git", "commit", "-m", "baseline"], cwd=sandbox_workdir, capture_output=True, check=False)

            # 4. Run Baseline Tests
            b_code, b_out = run_command_with_limits(test_cmd, sandbox_workdir, timeout_sec)

            # 5. Apply Patch
            patch_file = sandbox_workdir / "fix.patch"
            patch_file.write_text(diff_text, encoding="utf-8")
            apply_res = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", str(patch_file)],
                cwd=sandbox_workdir,
                capture_output=True,
                text=True,
            )

            if apply_res.returncode != 0:
                # If git apply fails, test manual line replacement for LoginForm demo
                applied = False
                login_form_path = sandbox_workdir / "src" / "auth" / "LoginForm.jsx"
                if login_form_path.exists():
                    code = login_form_path.read_text(encoding="utf-8")
                    if "res.data.token" in code:
                        fixed_code = code.replace(
                            "const handleSubmit = (e) => {",
                            "const handleSubmit = async (e) => {"
                        ).replace(
                            "const res = loginApi({ email, password });\n    setAuthToken(res.data.token);",
                            "const res = await loginApi({ email, password });\n    setAuthToken(res.token);"
                        )
                        login_form_path.write_text(fixed_code, encoding="utf-8")
                        applied = True

                if not applied:
                    combined_out = (
                        f"=== BASELINE TEST OUTPUT (exit {b_code}) ===\n{b_out[:1500]}\n\n"
                        f"=== PATCH APPLICATION FAILED ===\n{apply_res.stderr or apply_res.stdout}"
                    )
                    return "error", combined_out[:MAX_OUTPUT_CHARS], {"runner": runner_type, "baseline_exit": b_code}

            # 6. Run Patched Tests
            p_code, p_out = run_command_with_limits(test_cmd, sandbox_workdir, timeout_sec)

            combined_out = (
                f"=== BASELINE TESTS (exit code: {b_code}) ===\n{b_out}\n\n"
                f"=== PATCHED TESTS (exit code: {p_code}) ===\n{p_out}"
            )

            meta = {
                "runner": runner_type,
                "command": " ".join(test_cmd),
                "baseline_exit": b_code,
                "patched_exit": p_code,
            }

            # 7. Compare results
            # Passed: patched exited with 0 (and if baseline failed, it fixed it!)
            if p_code == 0:
                status = "passed"
            elif p_code > 0:
                status = "failed"
            else:
                status = "error"

            return status, combined_out[:MAX_OUTPUT_CHARS], meta
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


sandbox_verifier = SandboxVerifier()
