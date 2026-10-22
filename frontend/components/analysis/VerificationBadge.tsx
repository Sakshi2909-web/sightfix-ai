import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from "lucide-react";

interface Props {
  status: "passed" | "unverified" | "failed" | "error" | string;
}

export function VerificationBadge({ status }: Props) {
  switch (status) {
    case "passed":
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
          title="Verified: Automated sandbox tests passed without regressions."
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          Verified (Tests Passed)
        </span>
      );
    case "failed":
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30"
          title="Patch failed tests during sandboxed execution."
        >
          <XCircle className="w-3.5 h-3.5" />
          Failed Verification
        </span>
      );
    case "error":
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30"
          title="Sandbox execution error encountered."
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Sandbox Error
        </span>
      );
    case "unverified":
    default:
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700"
          title="Unverified: Sandbox did not detect an automated test suite or was not run."
        >
          <HelpCircle className="w-3.5 h-3.5" />
          Unverified Fix
        </span>
      );
  }
}
