from app.services.log_parser import log_parser, redact_secrets


def test_redact_secrets():
    raw = "User email is test.user@example.com and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz and api_key=ak_live_1234567890abcdef"
    redacted = redact_secrets(raw)
    assert "[REDACTED_EMAIL]" in redacted
    assert "test.user@example.com" not in redacted
    assert "[REDACTED_TOKEN]" in redacted
    assert "[REDACTED_API_KEY]" in redacted


def test_parse_js_stack_trace():
    logs = """
TypeError: Cannot read properties of undefined (reading 'token')
    at handleSubmit (src/auth/LoginForm.jsx:24:19)
    at HTMLFormElement.dispatch (node_modules/react-dom/cjs/react-dom.production.min.js:82:12)
    """
    findings = log_parser.parse(logs)
    assert len(findings.error_signatures) >= 1
    assert findings.error_signatures[0].error_type == "TypeError"
    assert "Cannot read properties of undefined" in findings.error_signatures[0].message

    assert len(findings.stack_frames) == 2
    # App code frame
    assert findings.stack_frames[0].is_app_code is True
    assert findings.stack_frames[0].file == "src/auth/LoginForm.jsx"
    assert findings.stack_frames[0].line == 24
    assert findings.stack_frames[0].function == "handleSubmit"

    # 3rd party frame
    assert findings.stack_frames[1].is_app_code is False
    assert findings.noise_filtered_count == 1


def test_parse_python_stack_trace():
    logs = """
2026-10-22 14:00:00 [ERROR] Internal server error
Traceback (most recent call last):
  File "backend/app/api/auth.py", line 45, in login_endpoint
    user = authenticate(email, password)
  File "/usr/local/lib/python3.11/site-packages/authlib/core.py", line 12, in authenticate
    raise ValueError("Invalid hash")
ValueError: Invalid hash
    """
    findings = log_parser.parse(logs)
    assert findings.first_error_timestamp is not None
    assert any(sig.error_type == "ValueError" for sig in findings.error_signatures)

    app_frames = [f for f in findings.stack_frames if f.is_app_code]
    assert len(app_frames) == 1
    assert app_frames[0].file == "backend/app/api/auth.py"
    assert app_frames[0].line == 45
    assert findings.noise_filtered_count >= 1
