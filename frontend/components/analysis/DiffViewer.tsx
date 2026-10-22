"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { Patch } from "@/lib/types";
import { VerificationBadge } from "./VerificationBadge";
import { api } from "@/lib/api";
import { Copy, Download, RefreshCw, Terminal, Check, Sparkles, AlertCircle } from "lucide-react";

const DiffEditor = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.DiffEditor),
  { ssr: false }
);

interface Props {
  patch: Patch | null;
  analysisId: string;
  onPatchUpdated?: (newPatch: Patch) => void;
}

export function DiffViewer({ patch, analysisId, onPatchUpdated }: Props) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [regenerating, setRegenerating] = useState(false);
  const [regenError, setRegenError] = useState<string | null>(null);
  const [showTestOutput, setShowTestOutput] = useState(false);

  if (!patch) {
    return (
      <div className="p-8 text-center text-zinc-500 border border-zinc-800 rounded-xl bg-zinc-900/40">
        <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-sm">No patch synthesized yet.</p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(patch.diff_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([patch.diff_text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sightfix-${patch.id.slice(0, 8)}.patch`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRegenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedback.trim()) return;
    setRegenerating(true);
    setRegenError(null);
    try {
      const updated = await api.regeneratePatch(analysisId, feedback);
      onPatchUpdated?.(updated);
      setFeedback("");
    } catch (err: any) {
      setRegenError(err.message || "Failed to regenerate patch");
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header card with status badge and actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-zinc-800 bg-zinc-900/80">
        <div className="flex items-center gap-3">
          <VerificationBadge status={patch.verification_status} />
          <span className="text-xs text-zinc-400 font-mono">
            Targets: {patch.target_files.join(", ")}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied" : "Copy Diff"}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition"
          >
            <Download className="w-3.5 h-3.5" />
            Download .patch
          </button>
          {patch.test_output && (
            <button
              onClick={() => setShowTestOutput(!showTestOutput)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition"
            >
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              {showTestOutput ? "Hide Tests" : "View Sandbox Tests"}
            </button>
          )}
        </div>
      </div>

      {/* Rationale card */}
      <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
        <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-1.5">
          Fix Rationale
        </h4>
        <p className="text-xs text-zinc-200 leading-relaxed">{patch.rationale}</p>
        {patch.suggested_tests && (
          <div className="mt-3 pt-3 border-t border-zinc-800/80">
            <h5 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-1">
              Suggested Regression Tests
            </h5>
            <pre className="p-2.5 rounded bg-zinc-950 border border-zinc-800/80 text-[11px] font-mono text-zinc-300 overflow-x-auto">
              {patch.suggested_tests}
            </pre>
          </div>
        )}
      </div>

      {/* Test Output Drawer */}
      {showTestOutput && patch.test_output && (
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950 font-mono text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-zinc-400 flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" />
              Isolated Sandbox Execution Log
            </span>
          </div>
          <pre className="p-3 rounded-lg bg-black text-zinc-300 text-[11px] overflow-x-auto whitespace-pre-wrap max-h-72">
            {patch.test_output}
          </pre>
        </div>
      )}

      {/* Diff View Box */}
      <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-950 min-h-[360px]">
        <div className="px-4 py-2 bg-zinc-900 border-b border-zinc-800 text-xs text-zinc-400 font-mono flex items-center justify-between">
          <span>Unified Diff Preview</span>
          <span className="text-[11px] text-zinc-500">git apply compatible</span>
        </div>
        <pre className="p-4 text-xs font-mono text-zinc-200 overflow-x-auto leading-relaxed">
          {patch.diff_text.split("\n").map((line, idx) => {
            const isAdd = line.startsWith("+") && !line.startsWith("+++");
            const isDel = line.startsWith("-") && !line.startsWith("---");
            const isHunk = line.startsWith("@@");
            return (
              <div
                key={idx}
                className={
                  isAdd
                    ? "bg-emerald-950/40 text-emerald-300 px-1 -mx-1"
                    : isDel
                    ? "bg-rose-950/40 text-rose-300 px-1 -mx-1"
                    : isHunk
                    ? "text-indigo-400 font-bold"
                    : "text-zinc-400"
                }
              >
                {line}
              </div>
            );
          })}
        </pre>
      </div>

      {/* Regenerate with Feedback Form */}
      <form onSubmit={handleRegenerate} className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
        <h4 className="text-xs font-semibold text-zinc-300 mb-2 flex items-center gap-1.5">
          <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
          Regenerate with Directed Feedback
        </h4>
        <div className="flex gap-2">
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="e.g. Also add null check for response.user or handle timeout error..."
            className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={regenerating || !feedback.trim()}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium transition flex items-center gap-1.5"
          >
            {regenerating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
            Regenerate
          </button>
        </div>
        {regenError && (
          <p className="text-xs text-rose-400 mt-2 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {regenError}
          </p>
        )}
      </form>
    </div>
  );
}
