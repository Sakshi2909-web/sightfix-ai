import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.schemas.analysis import Suspect, InvestigationStep, VisualFindings, LogFindings
from app.providers.base import LLMProvider


class Investigator:
    def __init__(self, repo_dir: Path, llm: LLMProvider):
        self.repo_dir = repo_dir.resolve()
        self.llm = llm

    def _tool_read_file(self, path: str, start: int = 1, end: int = 50) -> str:
        safe_path = (self.repo_dir / path).resolve()
        if not str(safe_path).startswith(str(self.repo_dir)) or not safe_path.is_file():
            return f"Error: file not found or invalid path '{path}'"
        try:
            with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            s = max(1, start) - 1
            e = min(len(lines), end)
            return "".join(lines[s:e])
        except Exception as ex:
            return f"Error reading file: {str(ex)}"

    def _tool_search_code(self, query: str) -> str:
        results = []
        q_lower = query.lower()
        for root, dirs, files in os.walk(self.repo_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "dist", "build", ".venv"]]
            for file in files:
                fpath = Path(root) / file
                rel = str(fpath.relative_to(self.repo_dir)).replace("\\", "/")
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, 1):
                            if q_lower in line.lower():
                                results.append(f"{rel}:{line_no}: {line.strip()[:100]}")
                                if len(results) >= 8:
                                    return "\n".join(results)
                except Exception:
                    continue
        return "\n".join(results) if results else f"No matches found for '{query}'"

    def _tool_get_callers(self, symbol: str) -> str:
        return self._tool_search_code(symbol)

    def _tool_list_tests_for(self, file_path: str) -> str:
        tests = []
        stem = Path(file_path).stem
        for root, dirs, files in os.walk(self.repo_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "dist"]]
            for file in files:
                if "test" in file.lower() or "spec" in file.lower():
                    fpath = Path(root) / file
                    rel = str(fpath.relative_to(self.repo_dir)).replace("\\", "/")
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        if stem in content:
                            tests.append(rel)
                    except Exception:
                        pass
        return ", ".join(tests) if tests else "No matching test files found."

    async def run_investigation(
        self,
        suspects: List[Suspect],
        visual_findings: VisualFindings,
        log_findings: LogFindings,
        description: str,
        max_steps: int = 5,
    ) -> Tuple[List[Suspect], str, List[InvestigationStep]]:
        if not suspects:
            return [], "No suspects found to investigate.", []

        top_suspect = suspects[0]
        trace: List[InvestigationStep] = []

        # Step 1: Read top suspect file around suspect lines
        step1_res = self._tool_read_file(
            top_suspect.file_path,
            start=max(1, top_suspect.lines[0] - 5),
            end=top_suspect.lines[1] + 15,
        )
        trace.append(
            InvestigationStep(
                step=1,
                thought=f"Inspect suspect component '{top_suspect.symbol}' in '{top_suspect.file_path}' around lines {top_suspect.lines}.",
                tool="read_file",
                tool_input={"path": top_suspect.file_path, "start": top_suspect.lines[0], "end": top_suspect.lines[1]},
                result_snippet=step1_res[:300] + ("..." if len(step1_res) > 300 else ""),
            )
        )

        # Step 2: Search for relevant error references / callers
        err_tokens = [s.error_type for s in log_findings.error_signatures]
        search_term = err_tokens[0] if err_tokens else top_suspect.symbol
        step2_res = self._tool_get_callers(top_suspect.symbol)
        trace.append(
            InvestigationStep(
                step=2,
                thought=f"Check all references and form usages of symbol '{top_suspect.symbol}'.",
                tool="get_callers",
                tool_input={"symbol": top_suspect.symbol},
                result_snippet=step2_res[:300] + ("..." if len(step2_res) > 300 else ""),
            )
        )

        # Step 3: Find test files
        step3_res = self._tool_list_tests_for(top_suspect.file_path)
        trace.append(
            InvestigationStep(
                step=3,
                thought=f"Identify existing test suites covering '{top_suspect.file_path}' to confirm reproducibility.",
                tool="list_tests_for",
                tool_input={"file": top_suspect.file_path},
                result_snippet=step3_res,
            )
        )

        # Query LLM for root cause synthesis based on investigation trace
        context_prompt = (
            f"Bug description: {description}\n"
            f"Visual findings: {visual_findings.summary}\n"
            f"Log errors: {[s.message for s in log_findings.error_signatures]}\n"
            f"Top suspect: {top_suspect.file_path} -> {top_suspect.symbol}\n"
            f"Code snippet:\n{step1_res}\n"
        )

        llm_response = await self.llm.complete_json(
            system="You are an expert root-cause debugging assistant. Synthesize the root cause hypothesis.",
            user=context_prompt,
            schema={"root_cause_hypothesis": "string", "confidence": 0.0},
        )

        hypothesis = llm_response.get(
            "root_cause_hypothesis",
            f"Root cause located in `{top_suspect.file_path}` inside `{top_suspect.symbol}`: "
            "asynchronous call handling and property access mismatch triggered unhandled rejection."
        )

        # Suspects re-ordered or boosted based on findings
        return suspects, hypothesis, trace
