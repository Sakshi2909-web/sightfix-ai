import React from "react";
import { Suspect } from "@/lib/types";
import { SuspectCard } from "./SuspectCard";
import { Layers } from "lucide-react";

interface Props {
  suspects: Suspect[];
  selectedSuspect: Suspect | null;
  onSelect: (suspect: Suspect) => void;
}

export function SuspectList({ suspects, selectedSuspect, onSelect }: Props) {
  if (!suspects || suspects.length === 0) {
    return (
      <div className="p-8 text-center border border-zinc-800 rounded-xl bg-zinc-900/40 text-zinc-500">
        <Layers className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-sm">No ranked suspects generated yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs text-zinc-400 px-1 mb-1">
        <span>Ranked Suspects ({suspects.length})</span>
        <span className="text-[11px] text-zinc-500">Sorted by Multi-Signal Fusion Score</span>
      </div>
      {suspects.map((suspect, idx) => (
        <SuspectCard
          key={`${suspect.file_path}-${suspect.symbol}-${idx}`}
          suspect={suspect}
          rank={idx + 1}
          isSelected={
            selectedSuspect?.file_path === suspect.file_path &&
            selectedSuspect?.symbol === suspect.symbol
          }
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
