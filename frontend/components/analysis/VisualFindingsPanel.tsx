import React from "react";
import { VisualFindings } from "@/lib/types";
import { Eye, AlertTriangle, CheckCircle, Tag, Layout } from "lucide-react";

interface Props {
  findings: VisualFindings | null;
  screenshotUrl?: string | null;
}

export function VisualFindingsPanel({ findings, screenshotUrl }: Props) {
  if (!findings) {
    return (
      <div className="p-8 text-center text-zinc-500 border border-zinc-800 rounded-xl bg-zinc-900/40">
        <Eye className="w-8 h-8 mx-auto mb-2 opacity-40" />
        <p className="text-sm">No visual findings available.</p>
      </div>
    );
  }

  const isLowQuality = findings.image_quality === "low" || findings.image_quality === "irrelevant";

  return (
    <div className="space-y-4">
      {/* Warning banner if weak or irrelevant visual evidence */}
      {isLowQuality && (
        <div className="flex items-center gap-2.5 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>
            Visual evidence confidence is {findings.image_quality}. Code ranking relies primarily on logs and AST signals.
          </span>
        </div>
      )}

      {/* Summary Card */}
      <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
        <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Eye className="w-3.5 h-3.5 text-cyan-400" />
          VLM Scene Understanding
        </h4>
        <p className="text-sm text-zinc-200 leading-relaxed">{findings.summary}</p>
      </div>

      {/* Screenshot with BBox preview if available */}
      {screenshotUrl && (
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Layout className="w-3.5 h-3.5 text-indigo-400" />
            Analyzed Screenshot Viewport
          </h4>
          <div className="relative rounded-lg overflow-hidden border border-zinc-800 bg-black flex justify-center">
            <img
              src={screenshotUrl}
              alt="Analyzed bug screenshot"
              className="max-h-[360px] object-contain w-auto"
            />
          </div>
        </div>
      )}

      {/* Anomalies & UI Elements Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Anomalies */}
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            Detected UI Anomalies ({findings.anomalies.length})
          </h4>
          {findings.anomalies.length === 0 ? (
            <p className="text-xs text-zinc-500">No layout or state anomalies detected.</p>
          ) : (
            <div className="space-y-2.5">
              {findings.anomalies.map((anom, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-lg bg-zinc-800/40 border border-zinc-800 text-xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono font-medium text-rose-300 capitalize">
                      {anom.kind.replace("_", " ")}
                    </span>
                    <span className="text-[10px] text-zinc-500 font-mono">
                      Conf: {(anom.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-zinc-400">{anom.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* UI Elements */}
        <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60">
          <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-blue-400" />
            Identified Interactive Elements ({findings.ui_elements.length})
          </h4>
          {findings.ui_elements.length === 0 ? (
            <p className="text-xs text-zinc-500">No interactive components recognized.</p>
          ) : (
            <div className="space-y-2">
              {findings.ui_elements.map((el, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-2 rounded-lg bg-zinc-800/40 border border-zinc-800 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-zinc-200">{el.label}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
                      {el.type}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded capitalize ${
                      el.state === "disabled"
                        ? "bg-amber-500/10 text-amber-300"
                        : el.state === "error"
                        ? "bg-rose-500/10 text-rose-300"
                        : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {el.state}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Likely component keywords */}
      {findings.likely_component_keywords.length > 0 && (
        <div className="p-3 rounded-xl border border-zinc-800 bg-zinc-900/60">
          <span className="text-xs text-zinc-400 font-medium block mb-2">
            Target Component Tokens:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {findings.likely_component_keywords.map((kw, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono"
              >
                {kw}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
