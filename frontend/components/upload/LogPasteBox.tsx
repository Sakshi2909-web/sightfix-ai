"use client";

import React from "react";
import { Terminal, Shield, Upload } from "lucide-react";

interface Props {
  value: string;
  onChange: (val: string) => void;
  onFileUpload: (file: File) => void;
}

export function LogPasteBox({ value, onChange, onFileUpload }: Props) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        if (event.target?.result) {
          onChange(event.target.result as string);
        }
      };
      reader.readAsText(file);
    }
  };

  const lineCount = value ? value.split("\n").length : 0;
  const errorHints = value ? (value.match(/(error|exception|fail|traceback)/gi) || []).length : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <label className="text-zinc-400 font-medium flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5 text-indigo-400" />
          Console / Server / Stack Trace Logs
        </label>
        <div className="flex items-center gap-2">
          {lineCount > 0 && (
            <span className="text-[10px] text-zinc-500 font-mono">
              {lineCount} lines ({errorHints} error signals)
            </span>
          )}
          <label className="cursor-pointer text-[11px] font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            <Upload className="w-3 h-3" />
            Upload .log file
            <input
              type="file"
              accept=".log,.txt"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        </div>
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={6}
        placeholder="Paste runtime stack trace, browser console errors, or server logs here...&#10;e.g. TypeError: Cannot read properties of undefined (reading 'token')&#10;    at handleSubmit (src/auth/LoginForm.jsx:18)"
        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 transition leading-relaxed resize-y"
      />

      <div className="flex items-center gap-1.5 text-[11px] text-zinc-500">
        <Shield className="w-3 h-3 text-emerald-500 flex-shrink-0" />
        <span>
          Secrets protection: Tokens, API keys, passwords, and emails are masked prior to model analysis.
        </span>
      </div>
    </div>
  );
}
