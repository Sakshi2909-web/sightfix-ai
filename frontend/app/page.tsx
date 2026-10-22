"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
  Sparkles,
  ArrowRight,
  Eye,
  Terminal,
  Cpu,
  ShieldAlert,
  CheckCircle2,
  GitPullRequest,
  Layers,
  Bug,
  Loader2,
} from "lucide-react";

export default function LandingPage() {
  const router = useRouter();
  const [loadingDemo, setLoadingDemo] = useState(false);

  const handleTryDemo = async () => {
    setLoadingDemo(true);
    try {
      // Find or seed demo repo
      const repos = await api.getRepos();
      const demoRepo = repos.find((r) => r.name === "demo_repo_login_bug");
      if (!demoRepo) {
        // Navigate to new analysis if demo repo not listed
        router.push("/analyze/new");
        return;
      }

      // Check existing analyses
      const analyses = await api.getAnalyses(demoRepo.id);
      if (analyses.length > 0) {
        router.push(`/analyses/${analyses[0].id}`);
        return;
      }

      // Start new analysis on demo repo
      const fd = new FormData();
      fd.append("repo_id", demoRepo.id);
      fd.append("title", "Sign in button unresponsive when submitting login form");
      fd.append(
        "description",
        "Clicking 'Sign in' does nothing when credentials are entered. The button stays active or disabled without any loading state or transition, and console shows TypeError."
      );
      fd.append("platform", "web");
      fd.append(
        "logs_text",
        `TypeError: Cannot read properties of undefined (reading 'token')\n    at handleSubmit (src/auth/LoginForm.jsx:18:22)`
      );

      const res = await api.createAnalysis(fd);
      router.push(`/analyses/${res.analysis_id}`);
    } catch {
      router.push("/analyze/new");
    } finally {
      setLoadingDemo(false);
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-56px)] bg-grid-pattern">
      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 pt-16 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-mono mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multimodal Bug Understanding & Automated Repair Intelligence</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-zinc-100 max-w-4xl mx-auto leading-tight sm:leading-none mb-6">
          Show the bug. <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-indigo-200 to-cyan-400">
            Get the verified fix.
          </span>
        </h1>

        <p className="text-base sm:text-lg text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Correlate UI screenshots, console traces, and codebase AST to pinpoint exact suspect
          functions with explicit multi-signal evidence and verified patches.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/analyze/new"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition shadow-lg shadow-indigo-500/25"
          >
            Start Analysis
            <ArrowRight className="w-4 h-4" />
          </Link>
          <button
            onClick={handleTryDemo}
            disabled={loadingDemo}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 font-semibold text-sm transition"
          >
            {loadingDemo ? <Loader2 className="w-4 h-4 animate-spin text-indigo-400" /> : <Bug className="w-4 h-4 text-cyan-400" />}
            {loadingDemo ? "Preparing Demo..." : "Try Live Demo (Login Bug)"}
          </button>
        </div>

        {/* Animated Mock Pipeline Flow */}
        <div className="mt-16 p-4 sm:p-6 rounded-2xl border border-zinc-800/80 bg-zinc-950/80 backdrop-blur shadow-2xl max-w-4xl mx-auto">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-500 pb-3 border-b border-zinc-800/80 mb-4">
            <span className="flex items-center gap-1.5 text-zinc-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              SightFix Pipeline Architecture
            </span>
            <span>Deterministic Fusion</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-left">
            <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <div className="flex items-center gap-2 text-cyan-400 mb-2">
                <Eye className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase">1. Visual</span>
              </div>
              <p className="text-xs text-zinc-300 font-mono">Sign in button unresponsive state</p>
              <span className="text-[10px] text-zinc-500 block mt-1">BBox [0.35, 0.54, 0.30, 0.07]</span>
            </div>

            <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <div className="flex items-center gap-2 text-rose-400 mb-2">
                <Terminal className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase">2. Stack Trace</span>
              </div>
              <p className="text-xs text-zinc-300 font-mono">Cannot read 'token'</p>
              <span className="text-[10px] text-zinc-500 block mt-1">LoginForm.jsx:18</span>
            </div>

            <div className="p-3.5 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <div className="flex items-center gap-2 text-indigo-400 mb-2">
                <Cpu className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase">3. Ranker</span>
              </div>
              <p className="text-xs text-zinc-300 font-mono">handleSubmit (0.94 score)</p>
              <span className="text-[10px] text-zinc-500 block mt-1">Stack + UI + BM25 Fusion</span>
            </div>

            <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30">
              <div className="flex items-center gap-2 text-emerald-400 mb-2">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase">4. Verified Patch</span>
              </div>
              <p className="text-xs text-emerald-300 font-mono">+ async/await fix</p>
              <span className="text-[10px] text-emerald-500/80 block mt-1">Sandbox Tests: Passed (4/4)</span>
            </div>
          </div>
        </div>
      </section>

      {/* 3 Core Pillars */}
      <section className="max-w-6xl mx-auto px-4 py-16 border-t border-zinc-800/80">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-zinc-100">
            Multi-Modal Signal Correlation
          </h2>
          <p className="text-sm text-zinc-400 mt-2">
            No hallucinated guesses. Every suspect ranks with explicit signal evidence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mb-4">
              <Eye className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100 mb-2">See It (Visual)</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Extracts UI anomalies, inactive buttons, clipped layouts, and rendered error banners
              via Vision-Language models with exact bounding boxes and OCR tokenization.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
              <Terminal className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100 mb-2">Trace It (Logs + AST)</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Language-aware regex parsers decode Python, JavaScript, Java, and Android stack traces,
              filtering framework noise and mapping frames directly to repo AST chunks.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-zinc-100 mb-2">Fix It (Verified Patch)</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Generates minimal unified diffs and executes isolated tests comparing baseline vs
              patched runs. "Verified" badges only display when test suites actually pass.
            </p>
          </div>
        </div>
      </section>

      {/* Honest Limits Section */}
      <section className="max-w-4xl mx-auto px-4 py-16 border-t border-zinc-800/80 mb-12">
        <div className="p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800">
          <div className="flex items-center gap-2 text-amber-400 text-sm font-semibold mb-3">
            <ShieldAlert className="w-4 h-4" />
            <span>Honesty & Product Boundaries: What SightFix Can and Cannot Do</span>
          </div>
          <ul className="space-y-2 text-xs text-zinc-400 leading-relaxed list-disc list-inside">
            <li>
              <strong className="text-zinc-200">Relative rank scores are not probabilities:</strong> A score of 0.85 means high relative rank across active signals, not an 85% statistical guarantee.
            </li>
            <li>
              <strong className="text-zinc-200">No fake verifications:</strong> If an automated test suite is not present in the repository, the fix is strictly labeled "Unverified Fix".
            </li>
            <li>
              <strong className="text-zinc-200">Visual evidence limitations:</strong> If screenshots are blank or unrelated, visual confidence drops to low/irrelevant and the system falls back to logs and lexical signals.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
