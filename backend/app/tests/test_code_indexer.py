from pathlib import Path
from app.services.code_indexer import parse_symbols, compute_content_hash


def test_parse_js_symbols():
    code = """
import React, { useState } from 'react';

export function LoginForm({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    loginUser(email, password);
  };

  return (
    <form onSubmit={handleSubmit}>
      <button type="submit">Sign in</button>
    </form>
  );
}
"""
    lines = code.strip().splitlines(keepends=True)
    chunks = parse_symbols("src/auth/LoginForm.jsx", lines, "JavaScript (React)")

    symbol_names = [c.symbol_name for c in chunks]
    assert "LoginForm" in symbol_names or "handleSubmit" in symbol_names
    for chunk in chunks:
        assert chunk.file_path == "src/auth/LoginForm.jsx"
        assert chunk.start_line > 0
        assert chunk.end_line >= chunk.start_line
        assert len(chunk.content_hash) > 0


def test_content_hash_deterministic():
    t1 = "const a = 1;"
    t2 = "const a = 1;"
    t3 = "const a = 2;"
    assert compute_content_hash(t1) == compute_content_hash(t2)
    assert compute_content_hash(t1) != compute_content_hash(t3)
