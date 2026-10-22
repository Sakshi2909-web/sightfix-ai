import re
from typing import List, Tuple, Dict, Any
from app.schemas.analysis import LogFindings, ErrorSignature, StackFrame

# Secret masking patterns
SECRET_PATTERNS = [
    (re.compile(r'(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{15,}'), r'\1[REDACTED_TOKEN]'),
    (re.compile(r'(?i)(api[_-]?key[\s:=]+)[\'"]?[a-zA-Z0-9_\-]{16,}[\'"]?'), r'\1"[REDACTED_API_KEY]"'),
    (re.compile(r'(?i)(password[\s:=]+)[\'"]?[^\s\'",]{4,}[\'"]?'), r'\1"[REDACTED_PASSWORD]"'),
    (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), r'[REDACTED_EMAIL]'),
]

# Regex patterns for various language stack traces
# JS / Node: at function (path/to/file.js:12:34) or at path/to/file.js:12:34
JS_STACK_REGEX = re.compile(
    r'^\s*at\s+(?:(?P<fn>[^\s(]+)\s+\()?(?P<file>[^():]+):(?P<line>\d+):(?P<col>\d+)\)?'
)

# Python: File "/path/to/file.py", line 42, in my_func
PY_STACK_REGEX = re.compile(
    r'^\s*File\s+"(?P<file>[^"]+)",\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<fn>.+))?'
)

# Java / Kotlin: at com.example.MyClass.myMethod(MyClass.java:123)
JAVA_STACK_REGEX = re.compile(
    r'^\s*at\s+(?P<fn>[a-zA-Z0-9_$.]+)\((?P<file>[a-zA-Z0-9_$.]+):(?P<line>\d+)\)'
)

# Generic Error Types: e.g. TypeError: ... , ValueError: ... , NullPointerException: ...
ERROR_HEAD_REGEX = re.compile(
    r'(?P<type>[a-zA-Z0-9_.]*(?:Error|Exception|Failure|Fault))(?::\s*(?P<msg>.*))?'
)

TIMESTAMP_REGEX = re.compile(
    r'\b(?:\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?|\d{2}:\d{2}:\d{2})\b'
)


def redact_secrets(text: str) -> str:
    """Masks tokens, API keys, passwords, and emails from log strings."""
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def is_third_party_frame(file_path: str) -> bool:
    """Checks if a frame points to external libraries like node_modules or site-packages."""
    norm = file_path.replace("\\", "/").lower()
    return any(
        skip in norm
        for skip in [
            "node_modules/",
            "site-packages/",
            "dist/",
            "<anonymous>",
            "internal/",
            "jdk/",
            "java.lang",
        ]
    )


def normalize_fingerprint(error_type: str, message: str) -> str:
    """Normalizes an error message into a fingerprint by removing specific hex/numbers/quotes."""
    cleaned = re.sub(r'0x[0-9a-fA-F]+', '0x...', message)
    cleaned = re.sub(r'\b\d+\b', 'N', cleaned)
    cleaned = re.sub(r'[\'"][^\'"]*[\'"]', 'STR', cleaned)
    return f"{error_type}:{cleaned.strip()}"


class LogParser:
    def parse(self, raw_logs: str) -> LogFindings:
        if not raw_logs or not raw_logs.strip():
            return LogFindings()

        safe_logs = redact_secrets(raw_logs)
        lines = safe_logs.splitlines()

        stack_frames: List[StackFrame] = []
        error_signatures: List[ErrorSignature] = []
        first_timestamp: str | None = None
        noise_filtered = 0

        # Scan for first timestamp
        for line in lines:
            ts_match = TIMESTAMP_REGEX.search(line)
            if ts_match and not first_timestamp:
                first_timestamp = ts_match.group(0)
                break

        for line in lines:
            line_str = line.strip()

            # Check JS/Node
            js_m = JS_STACK_REGEX.match(line)
            if js_m:
                fpath = js_m.group("file")
                is_app = not is_third_party_frame(fpath)
                if not is_app:
                    noise_filtered += 1
                stack_frames.append(
                    StackFrame(
                        file=fpath,
                        line=int(js_m.group("line")),
                        column=int(js_m.group("col")),
                        function=js_m.group("fn"),
                        raw=line_str,
                        is_app_code=is_app,
                    )
                )
                continue

            # Check Python
            py_m = PY_STACK_REGEX.match(line)
            if py_m:
                fpath = py_m.group("file")
                is_app = not is_third_party_frame(fpath)
                if not is_app:
                    noise_filtered += 1
                stack_frames.append(
                    StackFrame(
                        file=fpath,
                        line=int(py_m.group("line")),
                        function=py_m.group("fn"),
                        raw=line_str,
                        is_app_code=is_app,
                    )
                )
                continue

            # Check Java
            java_m = JAVA_STACK_REGEX.match(line)
            if java_m:
                fpath = java_m.group("file")
                is_app = not is_third_party_frame(fpath)
                if not is_app:
                    noise_filtered += 1
                stack_frames.append(
                    StackFrame(
                        file=fpath,
                        line=int(java_m.group("line")),
                        function=java_m.group("fn"),
                        raw=line_str,
                        is_app_code=is_app,
                    )
                )
                continue

            # Check Error Headings
            err_m = ERROR_HEAD_REGEX.search(line)
            if err_m:
                etype = err_m.group("type")
                emsg = (err_m.group("msg") or "").strip()
                fingerprint = normalize_fingerprint(etype, emsg)

                # Avoid duplicate signatures
                if not any(e.fingerprint == fingerprint for e in error_signatures):
                    error_signatures.append(
                        ErrorSignature(
                            error_type=etype,
                            message=emsg or line_str,
                            fingerprint=fingerprint,
                        )
                    )

        # Fallback if no error heading found but words like ERROR or FATAL exist
        if not error_signatures:
            for line in lines:
                if any(w in line.upper() for w in ["ERROR", "FATAL", "FAIL", "FAILED"]):
                    error_signatures.append(
                        ErrorSignature(
                            error_type="GenericError",
                            message=line.strip(),
                            fingerprint=normalize_fingerprint("GenericError", line.strip()),
                        )
                    )
                    break

        return LogFindings(
            error_signatures=error_signatures,
            stack_frames=stack_frames,
            first_error_timestamp=first_timestamp,
            noise_filtered_count=noise_filtered,
            raw_snippet="\n".join(lines[:50]),
        )


log_parser = LogParser()
