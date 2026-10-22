export async function loginApi(credentials) {
  if (credentials.email === "test@sightfix.dev" && credentials.password === "secret123") {
    return { token: "sightfix_valid_session_jwt_token_9981" };
  }
  throw new Error("Invalid username or password");
}
