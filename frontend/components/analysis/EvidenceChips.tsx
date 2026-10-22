import React from "react";
import { SuspectEvidence } from "@/lib/types";
import { Bug, Eye, Sparkles, FileText, GitCommit, Network } from "lucide-react";

interface Props {
  evidence: SuspectEvidence[];
}

export function EvidenceChips({ evidence }: Props) {
  if (!evidence || evidence.length === 0) return null;

  const getIcon = (type: string) => {
    switch (type) {
      case "stack_frame":
        return <Bug className="w-3 h-3 text-rose-400" />;
      case "ui_label":
        return <Eye className="w-3 h-3 text-cyan-400" />;
      case "semantic":
        return <Sparkles className="w-3 h-3 text-purple-400" />;
      case "lexical":
        return <FileText className="w-3 h-3 text-blue-400" />;
      case "git_recent":
        return <GitCommit className="w-3 h-3 text-amber-400" />;
      case "graph":
        return <Network className="w-3 h-3 text-emerald-400" />;
      default:
        return <Sparkles className="w-3 h-3 text-zinc-400" />;
    }
  };

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case "stack_frame":
        return "bg-rose-500/10 text-rose-300 border-rose-500/20";
      case "ui_label":
        return "bg-cyan-500/10 text-cyan-300 border-cyan-500/20";
      case "semantic":
        return "bg-purple-500/10 text-purple-300 border-purple-500/20";
      case "lexical":
        return "bg-blue-500/10 text-blue-300 border-blue-500/20";
      case "git_recent":
        return "bg-amber-500/10 text-amber-300 border-amber-500/20";
      case "graph":
        return "bg-emerald-500/10 text-emerald-300 border-emerald-500/20";
      default:
        return "bg-zinc-800 text-zinc-300 border-zinc-700";
    }
  };

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {evidence.map((ev, i) => (
        <span
          key={i}
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${getBadgeStyle(
            ev.type
          )}`}
          title={ev.detail}
        >
          {getIcon(ev.type)}
          <span className="capitalize">{ev.type.replace("_", " ")}</span>
          <span className="text-zinc-500">•</span>
          <span className="truncate max-w-[220px] text-zinc-400">{ev.detail}</span>
        </span>
      ))}
    </div>
  );
}
