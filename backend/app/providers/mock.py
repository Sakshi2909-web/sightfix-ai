import hashlib
import json
import math
from typing import List, Dict, Any
from app.providers.base import VLMProvider, LLMProvider, EmbeddingProvider
from app.schemas.analysis import VisualFindings, UIElement, Anomaly


def _hash_to_vector(text: str, dim: int = 128) -> List[float]:
    """Generates a deterministic normalized pseudo-embedding from text."""
    tokens = text.lower().split()
    vec = [0.0] * dim
    if not tokens:
        return [0.0] * dim
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(dim):
            bit = (h >> (i % 64)) & 1
            vec[i] += 1.0 if bit == 1 else -0.5
    # Normalize
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class MockVLMProvider(VLMProvider):
    async def describe_ui_issue(
        self, images: List[bytes], description: str, ocr_text: str
    ) -> VisualFindings:
        desc_lower = description.lower()
        is_login = "login" in desc_lower or "sign in" in desc_lower or "auth" in desc_lower or "login" in ocr_text.lower()

        if is_login:
            return VisualFindings(
                summary="The login page displays email and password fields. The 'Sign in' button appears visually inactive or unresponsive upon submission without any loading spinner or error feedback.",
                visible_error_text=["TypeError: Cannot read properties of undefined (reading 'token')"] if "error" in desc_lower or "token" in ocr_text else [],
                ui_elements=[
                    UIElement(type="input", label="Email Address", state="normal", bbox=[0.35, 0.38, 0.30, 0.06]),
                    UIElement(type="input", label="Password", state="normal", bbox=[0.35, 0.46, 0.30, 0.06]),
                    UIElement(type="button", label="Sign in", state="disabled", bbox=[0.35, 0.54, 0.30, 0.07]),
                ],
                anomalies=[
                    Anomaly(
                        kind="wrong_state",
                        description="Sign in button remains unresponsive after click event; state transition to loading or error banner did not trigger.",
                        confidence=0.92,
                    ),
                    Anomaly(
                        kind="missing_element",
                        description="Expected success redirect or validation feedback banner is absent from the viewport.",
                        confidence=0.85,
                    ),
                ],
                likely_component_keywords=["LoginForm", "handleSubmit", "auth", "signIn", "useAuth", "button"],
                image_quality="good",
            )
        else:
            return VisualFindings(
                summary=f"Analyzed visual view for: '{description[:80]}'. UI components detected with potential layout or interaction anomaly.",
                visible_error_text=["An unexpected error occurred"] if "error" in desc_lower else [],
                ui_elements=[
                    UIElement(type="button", label="Action", state="normal", bbox=[0.4, 0.5, 0.2, 0.06]),
                ],
                anomalies=[
                    Anomaly(
                        kind="layout_break",
                        description="Component rendered in unexpected state or unhandled exception boundary.",
                        confidence=0.75,
                    )
                ],
                likely_component_keywords=["App", "Component", "handler", "render"],
                image_quality="good" if len(images) > 0 else "low",
            )


class MockLLMProvider(LLMProvider):
    async def complete_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        # Check if patch schema requested
        if "diff_text" in schema or "diff" in user.lower() or "patch" in user.lower():
            diff_text = """--- a/src/auth/LoginForm.jsx
+++ b/src/auth/LoginForm.jsx
@@ -14,6 +14,8 @@ export function LoginForm({ onLoginSuccess }) {
-  const handleSubmit = (e) => {
-    e.preventDefault();
-    const res = loginApi({ email, password });
-    setAuthToken(res.data.token);
-    onLoginSuccess();
+  const handleSubmit = async (e) => {
+    e.preventDefault();
+    try {
+      setIsLoading(true);
+      const res = await loginApi({ email, password });
+      if (res && res.token) {
+        setAuthToken(res.token);
+        onLoginSuccess();
+      }
+    } catch (err) {
+      setError('Invalid credentials');
+    } finally {
+      setIsLoading(false);
+    }
   };
"""
            return {
                "target_files": ["src/auth/LoginForm.jsx"],
                "diff_text": diff_text.strip(),
                "rationale": "Made `handleSubmit` async, properly awaited `loginApi`, correctly accessed `res.token` instead of `res.data.token`, and wrapped in try-catch with loading and error states.",
                "suggested_tests": "test('handleSubmit properly awaits login and sets token', async () => { ... })",
            }

        # Check if root cause investigation requested
        if "root_cause_hypothesis" in schema or "investigation" in user.lower() or "hypothesis" in user.lower():
            return {
                "root_cause_hypothesis": "In `src/auth/LoginForm.jsx`, the `handleSubmit` event handler fails to await the asynchronous `loginApi` call and references `res.data.token` on a pending Promise, causing `TypeError: Cannot read properties of undefined (reading 'token')`.",
                "confidence": 0.94,
                "investigation_steps": [
                    {
                        "step": 1,
                        "thought": "Examine `LoginForm.jsx` around line 15-40 to inspect the `handleSubmit` implementation.",
                        "tool": "read_file",
                        "tool_input": {"path": "src/auth/LoginForm.jsx", "start": 10, "end": 45},
                        "result_snippet": "const handleSubmit = (e) => { e.preventDefault(); const res = loginApi(creds); setAuthToken(res.data.token); };",
                    },
                    {
                        "step": 2,
                        "thought": "Notice that `loginApi` is an async Promise returning `{ token }` inside `res`, but `res.data.token` was accessed without `await`.",
                        "tool": "search_code",
                        "tool_input": {"query": "loginApi"},
                        "result_snippet": "export async function loginApi(creds) { return { token: 'jwt-xyz' }; }",
                    },
                    {
                        "step": 3,
                        "thought": "Verified: `res` is a pending Promise when accessing `.token`, causing `Cannot read properties of undefined` and leaving the form unresponsive.",
                        "tool": "get_callers",
                        "tool_input": {"symbol": "handleSubmit"},
                        "result_snippet": "<form onSubmit={handleSubmit}> ... <button type='submit'>Sign in</button>",
                    },
                ],
            }

        return {"result": "ok", "message": "Mock completion response"}

    async def complete_text(self, system: str, user: str) -> str:
        user_lower = user.lower()
        if "diff" in user_lower or "patch" in user_lower:
            return """--- a/src/auth/LoginForm.jsx
+++ b/src/auth/LoginForm.jsx
@@ -18,6 +18,8 @@ export function LoginForm({ onLoginSuccess }) {
-  const handleSubmit = (e) => {
-    e.preventDefault();
-    const res = loginApi({ email, password });
-    setAuthToken(res.data.token);
-    onLoginSuccess();
+  const handleSubmit = async (e) => {
+    e.preventDefault();
+    try {
+      setIsLoading(true);
+      const res = await loginApi({ email, password });
+      if (res && res.token) {
+        setAuthToken(res.token);
+        onLoginSuccess();
+      }
+    } catch (err) {
+      setError('Invalid credentials');
+    } finally {
+      setIsLoading(false);
+    }
   };
"""
        return "Root cause identified: unhandled promise and missing async/await in form submission handler."


class MockEmbeddingProvider(EmbeddingProvider):
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [_hash_to_vector(t, dim=128) for t in texts]

    async def embed_images(self, images: List[bytes]) -> List[List[float]]:
        # Deterministic image vector based on image byte length and sample hash
        results = []
        for img in images:
            h = hashlib.sha256(img[:512]).hexdigest()
            results.append(_hash_to_vector(h, dim=128))
        return results
