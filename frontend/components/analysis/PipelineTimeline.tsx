import React from "react";
import { Check, Loader2, Circle, AlertCircle } from "lucide-react";

interface Props {
  currentStage: string;
  progress: number;
  status: "queued" | "running" | "completed" | "failed";
}

const STAGES = [
  { id: "Ingest", label: "1. Ingest" },
  { id: "Visual Understanding", label: "2. Visual Understanding" },
  { id: "Log Analysis", label: "3. Log Analysis" },
  { id: "Repo Indexing", label: "4. Repo Indexing" },
  { id: "Hybrid Retrieval", label: "5. Hybrid Retrieval" },
  { id: "Fusion Ranking", label: "6. Fusion Ranking" },
  { id: "Agentic Investigation", label: "7. Agentic Investigation" },
  { id: "Patch Generation", label: "8. Patch Generation" },
  { id: "Sandbox Verification", label: "9. Sandbox Verification" },
];

export function PipelineTimeline({ currentStage, progress, status }: Props) {
  const currentStageIndex = STAGES.findIndex(
    (s) => s.id.toLowerCase() === currentStage.toLowerCase()
  );

  return (
    <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-xl p-4 backdrop-blur">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-zinc-200">Analysis Pipeline</span>
          <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
            {progress}%
          </span>
        </div>
        <span
          className={`text-xs px-2.5 py-0.5 rounded-full font-medium capitalize ${
            status === "completed"
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : status === "failed"
              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
              : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse"
          }`}
        >
          {status}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden mb-5">
        <div
          className={`h-full transition-all duration-500 ${
            status === "completed"
              ? "bg-emerald-500"
              : status === "failed"
              ? "bg-rose-500"
              : "bg-gradient-to-r from-indigo-500 to-cyan-400"
          }`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        />
      </div>

      {/* Stage Steps */}
      <div className="space-y-2">
        {STAGES.map((stage, idx) => {
          const isDone =
            status === "completed" ||
            (currentStageIndex > idx && status !== "failed") ||
            (status === "failed" && currentStageIndex > idx);
          const isCurrent =
            status === "running" &&
            (currentStageIndex === idx || (currentStageIndex === -1 && idx === 0));
          const isFailed = status === "failed" && currentStageIndex === idx;

          return (
            <div
              key={stage.id}
              className={`flex items-center justify-between text-xs p-2 rounded-lg transition-colors ${
                isCurrent
                  ? "bg-indigo-500/10 text-indigo-300 font-medium border border-indigo-500/20"
                  : isDone
                  ? "text-zinc-300"
                  : "text-zinc-500"
              }`}
            >
              <div className="flex items-center gap-2.5">
                {isDone ? (
                  <div className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                    <Check className="w-2.5 h-2.5" />
                  </div>
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                ) : isFailed ? (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                ) : (
                  <Circle className="w-4 h-4 text-zinc-700" />
                )}
                <span>{stage.label}</span>
              </div>
              {isCurrent && <span className="text-[10px] text-indigo-400 font-mono">Running</span>}
              {isDone && <span className="text-[10px] text-zinc-500 font-mono">Done</span>}
              {isFailed && <span className="text-[10px] text-rose-400 font-mono">Failed</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
