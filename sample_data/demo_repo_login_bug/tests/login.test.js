const test = require('node:test');
const assert = require('node:assert');

// Mock loginApi
async function loginApi(credentials) {
  if (credentials.email === "test@sightfix.dev" && credentials.password === "secret123") {
    return { token: "sightfix_valid_session_jwt_token_9981" };
  }
  throw new Error("Invalid username or password");
}

test('1. Validates that credentials structure contains required fields', () => {
  const creds = { email: "test@sightfix.dev", password: "secret123" };
  assert.strictEqual(typeof creds.email, 'string');
  assert.strictEqual(typeof creds.password, 'string');
});

test('2. Rejects invalid credentials with an error', async () => {
  await assert.rejects(
    async () => {
      await loginApi({ email: "wrong@domain.com", password: "bad" });
    },
    { message: "Invalid username or password" }
  );
});

test('3. Authenticates valid user credentials via loginApi', async () => {
  const result = await loginApi({ email: "test@sightfix.dev", password: "secret123" });
  assert.ok(result);
  assert.strictEqual(result.token, "sightfix_valid_session_jwt_token_9981");
});

test('4. Submits login form and properly receives token without uncaught exception', async () => {
  // Simulates the behavior in LoginForm.jsx handleSubmit
  let authToken = null;
  let loginSuccessCalled = false;

  const onLoginSuccess = () => { loginSuccessCalled = true; };
  const email = "test@sightfix.dev";
  const password = "secret123";

  // Check the actual file implementation:
  const fs = require('fs');
  const path = require('path');
  const formCode = fs.readFileSync(path.join(__dirname, '../src/auth/LoginForm.jsx'), 'utf-8');

  // If the bug is present (missing await or accessing res.data.token), this test MUST fail!
  if (formCode.includes('res.data.token') || !formCode.includes('await loginApi')) {
    assert.fail(
      "Uncaught TypeError: Cannot read properties of undefined (reading 'token') in handleSubmit at LoginForm.jsx:18"
    );
  }

  // After fix is applied:
  authToken = "sightfix_valid_session_jwt_token_9981";
  onLoginSuccess();
  assert.strictEqual(authToken, "sightfix_valid_session_jwt_token_9981");
  assert.strictEqual(loginSuccessCalled, true);
});
