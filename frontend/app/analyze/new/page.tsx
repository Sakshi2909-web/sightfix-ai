"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { RepoPicker } from "@/components/upload/RepoPicker";
import { Dropzone } from "@/components/upload/Dropzone";
import { ImagePreview } from "@/components/upload/ImagePreview";
import { LogPasteBox } from "@/components/upload/LogPasteBox";
import { api } from "@/lib/api";
import { Repo } from "@/lib/types";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  Loader2,
  AlertCircle,
  FileText,
  Image as ImageIcon,
  Layers,
} from "lucide-react";

export default function NewAnalysisPage() {
  const router = useRouter();
  const store = useAnalysisStore();

  const [repos, setRepos] = useState<Repo[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getRepos()
      .then((data) => {
        setRepos(data);
        if (data.length > 0 && !store.selectedRepoId) {
          store.setSelectedRepoId(data[0].id);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoadingRepos(false));
  }, []);

  const handleRepoCreated = (newRepo: Repo) => {
    setRepos((prev) => [newRepo, ...prev]);
    store.setSelectedRepoId(newRepo.id);
  };

  const handleStartAnalysis = async () => {
    if (!store.selectedRepoId) {
      setError("Please select a repository first.");
      return;
    }
    if (!store.title.trim() || !store.description.trim()) {
      setError("Please provide a title and bug description.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const fd = new FormData();
      fd.append("repo_id", store.selectedRepoId);
      fd.append("title", store.title);
      fd.append("description", store.description);
      fd.append("platform", store.platform);

      for (const img of store.screenshots) {
        fd.append("screenshots", img);
      }
      if (store.video) {
        fd.append("video", store.video);
      }
      if (store.logsText.trim()) {
        fd.append("logs_text", store.logsText);
      }
      if (store.logsFile) {
        fd.append("logs_file", store.logsFile);
      }

      const res = await api.createAnalysis(fd);
      store.reset();
      router.push(`/analyses/${res.analysis_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start analysis");
      setSubmitting(false);
    }
  };

  const selectedRepo = repos.find((r) => r.id === store.selectedRepoId);

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Stepper Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          Create New Multimodal Bug Analysis
        </h1>
        <p className="text-xs text-zinc-400 mt-1">
          Combine visual symptoms, logs, and repo AST to synthesize a verified fix.
        </p>

        {/* Stepper Dots */}
        <div className="flex items-center gap-2 mt-6">
          {[
            { step: 1, title: "1. Repository" },
            { step: 2, title: "2. Evidence" },
            { step: 3, title: "3. Review & Run" },
          ].map((item) => (
            <React.Fragment key={item.step}>
              <button
                type="button"
                onClick={() => store.setStep(item.step)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  store.step === item.step
                    ? "bg-indigo-600 text-white font-semibold"
                    : store.step > item.step
                    ? "bg-zinc-800 text-zinc-200"
                    : "text-zinc-500 hover:text-zinc-400"
                }`}
              >
                {store.step > item.step ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : null}
                <span>{item.title}</span>
              </button>
              {item.step < 3 && <span className="text-zinc-700">/</span>}
            </React.Fragment>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Step 1: Repository */}
      {store.step === 1 && (
        <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/60 backdrop-blur space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-zinc-200 mb-1">
              Select or Upload Repository
            </h3>
            <p className="text-xs text-zinc-400">
              SightFix indexes source code chunks, symbols, and build manifests for sandboxed test execution.
            </p>
          </div>

          {loadingRepos ? (
            <div className="p-8 text-center text-zinc-500 flex items-center justify-center gap-2 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
              Loading repositories...
            </div>
          ) : (
            <RepoPicker
              repos={repos}
              selectedRepoId={store.selectedRepoId}
              onSelect={store.setSelectedRepoId}
              onRepoCreated={handleRepoCreated}
            />
          )}

          <div className="flex justify-end pt-4 border-t border-zinc-800/80">
            <button
              type="button"
              disabled={!store.selectedRepoId}
              onClick={() => store.setStep(2)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition"
            >
              Continue to Evidence
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Evidence */}
      {store.step === 2 && (
        <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/60 backdrop-blur space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-zinc-200 mb-1">
              Upload Multimodal Bug Evidence
            </h3>
            <p className="text-xs text-zinc-400">
              Provide visual screenshots, screen recordings, logs, and a description of what failed.
            </p>
          </div>

          {/* Title & Platform */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-2">
              <label className="text-xs text-zinc-400 block mb-1">Bug Report Title</label>
              <input
                type="text"
                value={store.title}
                onChange={(e) => store.setTitle(e.target.value)}
                placeholder="e.g. Sign in button unresponsive when submitting login form"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-zinc-400 block mb-1">Platform</label>
              <select
                value={store.platform}
                onChange={(e) => store.setPlatform(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-indigo-500"
              >
                <option value="web">Web</option>
                <option value="android">Android</option>
                <option value="ios">iOS</option>
                <option value="backend">Backend Service</option>
                <option value="desktop">Desktop</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="text-xs text-zinc-400 block mb-1">
              Natural Language Bug Description
            </label>
            <textarea
              value={store.description}
              onChange={(e) => store.setDescription(e.target.value)}
              rows={3}
              placeholder="Describe user behavior, expected vs actual result, and any reproduction steps..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-indigo-500 resize-y"
            />
          </div>

          {/* Screenshots dropzone & previews */}
          <div>
            <label className="text-xs text-zinc-400 block mb-1.5 font-medium">
              Screenshots / Screen Recordings
            </label>
            <Dropzone
              onImagesSelected={(files) => files.forEach(store.addScreenshot)}
              onVideoSelected={store.setVideo}
            />
            <div className="mt-3">
              <ImagePreview
                urls={store.screenshotUrls}
                onRemove={store.removeScreenshot}
              />
            </div>
          </div>

          {/* Logs */}
          <LogPasteBox
            value={store.logsText}
            onChange={store.setLogsText}
            onFileUpload={store.setLogsFile}
          />

          <div className="flex items-center justify-between pt-4 border-t border-zinc-800/80">
            <button
              type="button"
              onClick={() => store.setStep(1)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-medium hover:bg-zinc-800 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back
            </button>
            <button
              type="button"
              onClick={() => store.setStep(3)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition"
            >
              Review & Run
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Review & Run */}
      {store.step === 3 && (
        <div className="p-6 rounded-2xl border border-zinc-800 bg-zinc-950/60 backdrop-blur space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-zinc-200 mb-1">
              Review Analysis Configuration
            </h3>
            <p className="text-xs text-zinc-400">
              Confirm report details before launching the multi-stage localization and sandbox repair pipeline.
            </p>
          </div>

          {/* Review Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60 space-y-2">
              <span className="text-zinc-500 font-semibold uppercase tracking-wider block text-[10px]">
                Target Repository
              </span>
              <div className="flex items-center gap-2 text-zinc-200 font-medium">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>{selectedRepo?.name || "None selected"}</span>
              </div>
              <p className="text-zinc-500 font-mono text-[11px]">
                Branch: {selectedRepo?.default_branch || "main"}
              </p>
            </div>

            <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/60 space-y-2">
              <span className="text-zinc-500 font-semibold uppercase tracking-wider block text-[10px]">
                Collected Evidence
              </span>
              <div className="flex items-center gap-4 text-zinc-300">
                <span className="flex items-center gap-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
                  {store.screenshots.length} screenshot(s)
                </span>
                <span className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-rose-400" />
                  {store.logsText.trim() || store.logsFile ? "Logs attached" : "No logs"}
                </span>
              </div>
              <p className="text-zinc-500 text-[11px]">Platform: {store.platform}</p>
            </div>
          </div>

          <div className="p-4 rounded-xl border border-zinc-800 bg-zinc-900/40 text-xs space-y-1">
            <span className="text-zinc-500 font-semibold uppercase tracking-wider block text-[10px]">
              Issue Description
            </span>
            <div className="font-semibold text-zinc-200">{store.title || "Untitled Issue"}</div>
            <p className="text-zinc-400 leading-relaxed">{store.description || "No description provided."}</p>
          </div>

          {/* Privacy & Transparency Notice */}
          <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-500/20 flex items-start gap-3 text-xs text-indigo-300">
            <ShieldCheck className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-indigo-200 block mb-0.5">Privacy Notice</strong>
              Log secrets (Bearer tokens, API keys, passwords, emails) are redacted before analysis.
              Diffs are tested in a network-disabled sandbox before presenting the verified patch.
            </div>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-zinc-800/80">
            <button
              type="button"
              onClick={() => store.setStep(2)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-medium hover:bg-zinc-800 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={handleStartAnalysis}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs transition shadow-lg shadow-indigo-500/25"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {submitting ? "Initiating Pipeline..." : "Start Analysis"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
