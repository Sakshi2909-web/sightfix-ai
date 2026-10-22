import React from "react";
import { LogFindings, StackFrame } from "@/lib/types";
import { Terminal, ShieldCheck, Clock, FileCode } from "lucide-react";

interface Props {
  findings: LogFindings | null;
  onSelectFrame?: (frame: StackFrame) => void;
}

export function LogInsightsPanel({ findings, onSelectFrame }: Props) {
  if (!findings) {
    return (
      <div className="p-8 text-center text-zinc-500 border border-zinc-800 rounded-xl bg-zinc-900/40">
        <Terminal className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-sm">No log insights available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Metrics Row */}
      <div className="flex items-center gap-3 flex-wrap">
        {findings.first_error_timestamp && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-300">
            <Clock className="w-3.5 h-3.5 text-zinc-400" />
            <span>First Signal:</span>
            <span className="font-mono text-indigo-400">{findings.first_error_timestamp}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Noise Filtered:</span>
          <span className="font-mono text-emerald-400">
            {findings.noise_filtered_count} external frames
          </span>
        </div>
      </div>

      {/* Error Signatures */}
      <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
        <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Error Signatures ({findings.error_signatures.length})
        </h4>
        <div className="space-y-2">
          {findings.error_signatures.map((sig, i) => (
            <div
              key={i}
              className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs"
            >
              <div className="font-mono font-bold text-rose-400 mb-1">{sig.error_type}</div>
              <div className="text-zinc-200 font-mono text-[11px] break-all">{sig.message}</div>
              <div className="text-[10px] text-zinc-500 font-mono mt-1">
                Fingerprint: {sig.fingerprint}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Parsed Stack Frames */}
      <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
        <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Stack Frames ({findings.stack_frames.length})
        </h4>
        <div className="space-y-1.5 font-mono text-xs">
          {findings.stack_frames.map((frame, i) => (
            <div
              key={i}
              onClick={() => frame.is_app_code && onSelectFrame?.(frame)}
              className={`p-2.5 rounded-lg border transition-all ${
                frame.is_app_code
                  ? "bg-zinc-800/80 border-indigo-500/30 text-zinc-100 hover:border-indigo-400 cursor-pointer"
                  : "bg-zinc-950/40 border-zinc-900 text-zinc-500"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="truncate">
                  {frame.function ? `at ${frame.function} (` : "at "}
                  <span className={frame.is_app_code ? "text-indigo-300 font-semibold" : ""}>
                    {frame.file}
                  </span>
                  {frame.line ? `:${frame.line}` : ""}
                  {frame.column ? `:${frame.column}` : ""}
                  {frame.function ? ")" : ""}
                </span>
                {frame.is_app_code && (
                  <span className="text-[10px] flex-shrink-0 px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 ml-2">
                    App Code
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
