"use client";

import React, { useState } from "react";
import { useParams } from "next/navigation";
import { useAnalysisStream } from "@/lib/sse";
import { api } from "@/lib/api";
import { Suspect, StackFrame, Patch } from "@/lib/types";

import { PipelineTimeline } from "@/components/analysis/PipelineTimeline";
import { SuspectList } from "@/components/analysis/SuspectList";
import { VisualFindingsPanel } from "@/components/analysis/VisualFindingsPanel";
import { LogInsightsPanel } from "@/components/analysis/LogInsightsPanel";
import { CodeViewer } from "@/components/analysis/CodeViewer";
import { DiffViewer } from "@/components/analysis/DiffViewer";
import { VerificationBadge } from "@/components/analysis/VerificationBadge";
import { formatTimeAgo } from "@/lib/utils";

import {
  Sparkles,
  Eye,
  Terminal,
  Layers,
  FileCode,
  GitPullRequest,
  Download,
  ThumbsUp,
  ThumbsDown,
  RotateCw,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  X,
} from "lucide-react";

export default function AnalysisDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: analysis, isConnected, error } = useAnalysisStream(id);

  const [activeTab, setActiveTab] = useState<
    "overview" | "visual" | "logs" | "suspects" | "trace" | "patch"
  >("overview");

  const [selectedSuspect, setSelectedSuspect] = useState<Suspect | null>(null);
  const [activeCodeFile, setActiveCodeFile] = useState<{
    path: string;
    lines?: [number, number];
  } | null>(null);

  // Feedback state
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackThumbs, setFeedbackThumbs] = useState<boolean | null>(null);

  const handleSelectSuspect = (suspect: Suspect) => {
    setSelectedSuspect(suspect);
    setActiveCodeFile({ path: suspect.file_path, lines: suspect.lines });
  };

  const handleSelectFrame = (frame: StackFrame) => {
    setActiveCodeFile({
      path: frame.file,
      lines: frame.line ? [frame.line, frame.line] : undefined,
    });
  };

  const handleFeedback = async (correct: boolean) => {
    setFeedbackThumbs(correct);
    try {
      await api.submitFeedback(id, correct);
      setFeedbackSent(true);
    } catch {}
  };

  const handleRerun = async () => {
    try {
      await api.rerunAnalysis(id);
    } catch (err: any) {
      alert(err.message || "Failed to trigger rerun");
    }
  };

  const latestPatch: Patch | null = analysis?.patches?.[0] || null;

  if (error && !analysis) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-zinc-100">Analysis Not Found</h2>
        <p className="text-xs text-zinc-400 mt-1">{error}</p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center text-zinc-400 text-xs flex items-center justify-center gap-2">
        <RotateCw className="w-4 h-4 animate-spin text-indigo-500" />
        Connecting to SightFix analysis stream...
      </div>
    );
  }

  return (
    <div className="max-w-[1600px] mx-auto px-4 py-6">
      {/* Top Bar Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-zinc-800/80 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              Analysis: <span className="font-mono text-zinc-300">{id.slice(0, 8)}...</span>
            </h1>
            <VerificationBadge status={latestPatch?.verification_status || "unverified"} />
            {isConnected && (
              <span className="flex items-center gap-1.5 text-[11px] font-mono text-emerald-400 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live SSE Stream
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Created {formatTimeAgo(analysis.created_at)} • Stage:{" "}
            <span className="text-indigo-400 font-mono font-medium">{analysis.stage}</span> (
            {analysis.progress}%)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRerun}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 text-xs font-medium transition"
            title="Re-run analysis with fresh weights"
          >
            <RotateCw className="w-3.5 h-3.5" />
            Re-run Analysis
          </button>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/analyses/${id}/export?format=md`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 text-xs font-medium transition"
          >
            <Download className="w-3.5 h-3.5" />
            Export Report (.md)
          </a>
        </div>
      </div>

      {/* Main Grid: Left Timeline | Center Tabs | Right Code Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Rail: Timeline (3 Cols) */}
        <div className="lg:col-span-3 space-y-4">
          <PipelineTimeline
            currentStage={analysis.stage}
            progress={analysis.progress}
            status={analysis.status as any}
          />

          {/* Feedback Evaluation Card */}
          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60 backdrop-blur text-xs">
            <span className="font-semibold text-zinc-300 block mb-1">
              Benchmark Accuracy Feedback
            </span>
            <p className="text-zinc-500 mb-3 text-[11px]">
              Was the correct faulty file in the top 3 ranked suspects?
            </p>
            {feedbackSent ? (
              <div className="flex items-center gap-1.5 text-emerald-400 font-medium text-xs">
                <CheckCircle2 className="w-4 h-4" />
                Thank you! Feedback recorded for evaluation.
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleFeedback(true)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition"
                >
                  <ThumbsUp className="w-3 h-3 text-emerald-400" />
                  Yes
                </button>
                <button
                  onClick={() => handleFeedback(false)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 transition"
                >
                  <ThumbsDown className="w-3 h-3 text-rose-400" />
                  No
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Center Rail: Analysis Findings & Tabs (activeCodeFile ? 5 cols : 9 cols) */}
        <div className={activeCodeFile ? "lg:col-span-5" : "lg:col-span-9"}>
          {/* Tabs bar */}
          <div className="flex items-center gap-1 p-1 bg-zinc-900 border border-zinc-800 rounded-xl mb-4 overflow-x-auto">
            {[
              { id: "overview", label: "Overview", icon: Sparkles },
              { id: "visual", label: "Visual Findings", icon: Eye },
              { id: "logs", label: "Log Insights", icon: Terminal },
              { id: "suspects", label: `Suspects (${analysis.suspects?.length || 0})`, icon: Layers },
              { id: "trace", label: "Agentic Trace", icon: FileCode },
              { id: "patch", label: "Verified Patch", icon: GitPullRequest },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition whitespace-nowrap ${
                    isActive
                      ? "bg-zinc-800 text-zinc-100 font-semibold shadow-sm"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab 1: Overview */}
          {activeTab === "overview" && (
            <div className="space-y-4">
              {/* Root Cause Hypothesis Card */}
              <div className="p-5 rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-indigo-950/20 to-zinc-950 p-5">
                <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider block mb-1">
                  Synthesized Root Cause Hypothesis
                </span>
                <p className="text-sm text-zinc-100 font-medium leading-relaxed">
                  {analysis.root_cause_hypothesis || "Investigation in progress..."}
                </p>
              </div>

              {/* Top Suspects preview */}
              <div>
                <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                  Top Suspect Locations
                </h3>
                <SuspectList
                  suspects={(analysis.suspects || []).slice(0, 3)}
                  selectedSuspect={selectedSuspect}
                  onSelect={handleSelectSuspect}
                />
              </div>

              {/* Quick Patch Preview */}
              {latestPatch && (
                <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-950/60">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                      <GitPullRequest className="w-3.5 h-3.5 text-indigo-400" />
                      Generated Patch Summary
                    </span>
                    <button
                      onClick={() => setActiveTab("patch")}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      View Full Diff →
                    </button>
                  </div>
                  <p className="text-xs text-zinc-400 mb-2">{latestPatch.rationale}</p>
                  <div className="font-mono text-[11px] text-zinc-500">
                    Targets: {latestPatch.target_files.join(", ")}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Visual Findings */}
          {activeTab === "visual" && (
            <VisualFindingsPanel findings={analysis.visual_findings as any} />
          )}

          {/* Tab 3: Log Insights */}
          {activeTab === "logs" && (
            <LogInsightsPanel
              findings={analysis.log_findings as any}
              onSelectFrame={handleSelectFrame}
            />
          )}

          {/* Tab 4: Suspects */}
          {activeTab === "suspects" && (
            <SuspectList
              suspects={analysis.suspects || []}
              selectedSuspect={selectedSuspect}
              onSelect={handleSelectSuspect}
            />
          )}

          {/* Tab 5: Agentic Investigation Trace */}
          {activeTab === "trace" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-zinc-400 px-1 mb-1">
                <span>Agentic RAG Investigation Steps</span>
                <span className="text-[11px] text-zinc-500">Autonomous tool execution</span>
              </div>
              {!analysis.investigation_trace || analysis.investigation_trace.length === 0 ? (
                <p className="text-xs text-zinc-500 p-8 text-center border border-zinc-800 rounded-xl bg-zinc-900/40">
                  No trace recorded.
                </p>
              ) : (
                analysis.investigation_trace.map((step: any, i: number) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl border border-zinc-800 bg-zinc-900/60 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded bg-indigo-500/20 text-indigo-400 font-mono font-semibold flex items-center justify-center text-[10px]">
                          {step.step}
                        </span>
                        <span className="font-mono font-semibold text-zinc-200">
                          tool: {step.tool}
                        </span>
                      </div>
                      {step.tool_input && (
                        <span className="text-[10px] text-zinc-500 font-mono truncate max-w-[200px]">
                          {JSON.stringify(step.tool_input)}
                        </span>
                      )}
                    </div>
                    <p className="text-zinc-300">{step.thought}</p>
                    {step.result_snippet && (
                      <pre className="p-2.5 rounded bg-zinc-950 border border-zinc-800/80 font-mono text-[11px] text-zinc-400 overflow-x-auto whitespace-pre-wrap">
                        {step.result_snippet}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 6: Patch & Verification */}
          {activeTab === "patch" && (
            <DiffViewer
              patch={latestPatch}
              analysisId={id}
              onPatchUpdated={() => {
                api.getAnalysis(id);
              }}
            />
          )}
        </div>

        {/* Right Rail: Code Viewer Drawer (4 Cols if active) */}
        {activeCodeFile && (
          <div className="lg:col-span-4 sticky top-20 space-y-2">
            <div className="flex items-center justify-between text-xs text-zinc-400">
              <span className="font-semibold flex items-center gap-1.5 text-zinc-200">
                <FileCode className="w-4 h-4 text-indigo-400" />
                Code Inspection Drawer
              </span>
              <button
                onClick={() => setActiveCodeFile(null)}
                className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-200"
                title="Close drawer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="h-[600px]">
              <CodeViewer
                repoId={analysis.report_id ? id : ""}
                filePath={activeCodeFile.path}
                highlightLines={activeCodeFile.lines}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
