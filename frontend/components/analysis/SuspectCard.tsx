import React from "react";
import { Suspect } from "@/lib/types";
import { EvidenceChips } from "./EvidenceChips";
import { FileCode, ArrowRight, HelpCircle } from "lucide-react";

interface Props {
  suspect: Suspect;
  rank: number;
  isSelected: boolean;
  onSelect: (suspect: Suspect) => void;
}

export function SuspectCard({ suspect, rank, isSelected, onSelect }: Props) {
  const percentage = Math.round(suspect.score * 100);

  return (
    <div
      onClick={() => onSelect(suspect)}
      className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
        isSelected
          ? "bg-indigo-950/20 border-indigo-500/50 shadow-lg shadow-indigo-500/5"
          : "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/90"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5 min-w-0">
          <span className="flex-shrink-0 w-5 h-5 rounded-md bg-zinc-800 text-zinc-400 text-xs font-mono font-semibold flex items-center justify-center">
            #{rank}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-mono text-xs font-semibold text-zinc-100 truncate">
                {suspect.file_path}
              </span>
              <span className="text-xs px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">
                {suspect.symbol}
              </span>
              <span className="text-[11px] text-zinc-500 font-mono">
                L{suspect.lines[0]}-{suspect.lines[1]}
              </span>
            </div>
          </div>
        </div>

        {/* Relative Rank Score Bar */}
        <div className="flex flex-col items-end flex-shrink-0">
          <div className="flex items-center gap-1">
            <span className="text-xs font-mono font-bold text-indigo-400">
              {suspect.score.toFixed(2)}
            </span>
            <span
              className="text-zinc-500 hover:text-zinc-400 cursor-help"
              title="Not a probability. This is a multi-signal relative ranking score."
            >
              <HelpCircle className="w-3 h-3" />
            </span>
          </div>
          <div className="w-16 h-1.5 bg-zinc-800 rounded-full mt-1 overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Multi-modal Evidence Chips */}
      <EvidenceChips evidence={suspect.evidence} />
    </div>
  );
}
