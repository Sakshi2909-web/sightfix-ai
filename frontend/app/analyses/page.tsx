"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Analysis } from "@/lib/types";
import { VerificationBadge } from "@/components/analysis/VerificationBadge";
import { formatTimeAgo } from "@/lib/utils";
import { History, Search, ArrowRight, Loader2, Sparkles } from "lucide-react";

export default function AnalysesHistoryPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    api
      .getAnalyses()
      .then(setAnalyses)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = analyses.filter((a) => {
    const matchesStatus = statusFilter === "all" || a.status === statusFilter;
    const topSuspect = a.suspects?.[0]?.file_path || "";
    const matchesSearch =
      searchTerm === "" ||
      a.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      topSuspect.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.stage && a.stage.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Analysis History
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Browse previous multimodal localization runs, suspect rankings, and test results.
          </p>
        </div>

        <Link
          href="/analyze/new"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
        >
          <Sparkles className="w-3.5 h-3.5" />
          New Analysis
        </Link>
      </div>

      {/* Filter Row */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by file path, ID, or stage..."
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-9 pr-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-zinc-950 border border-zinc-800 rounded-xl px-3 py-2 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500"
        >
          <option value="all">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="queued">Queued</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Table */}
      <div className="border border-zinc-800 rounded-2xl overflow-hidden bg-zinc-950/60 backdrop-blur">
        {loading ? (
          <div className="p-12 text-center text-zinc-500 flex items-center justify-center gap-2 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
            Loading analysis records...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-zinc-500 text-xs">
            No analyses match the criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-900/80 border-b border-zinc-800 text-zinc-400 font-mono text-[11px]">
                <tr>
                  <th className="py-3 px-4">Analysis</th>
                  <th className="py-3 px-4">Status & Stage</th>
                  <th className="py-3 px-4">Top Suspect</th>
                  <th className="py-3 px-4">Verification</th>
                  <th className="py-3 px-4">Created</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60">
                {filtered.map((item) => {
                  const topSuspect = item.suspects?.[0];
                  const latestPatch = item.patches?.[0];

                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-zinc-900/50 transition cursor-pointer"
                    >
                      <td className="py-3.5 px-4">
                        <Link href={`/analyses/${item.id}`} className="block">
                          <span className="font-mono font-medium text-zinc-200 block truncate max-w-[200px]">
                            {item.id.slice(0, 8)}...
                          </span>
                          <span className="text-[10px] text-zinc-500 font-mono">
                            Progress: {item.progress}%
                          </span>
                        </Link>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium capitalize ${
                            item.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400"
                              : item.status === "failed"
                              ? "bg-rose-500/10 text-rose-400"
                              : "bg-indigo-500/10 text-indigo-400"
                          }`}
                        >
                          {item.stage || item.status}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        {topSuspect ? (
                          <div className="font-mono">
                            <span className="text-zinc-200 font-medium truncate block max-w-[240px]">
                              {topSuspect.file_path}
                            </span>
                            <span className="text-[10px] text-indigo-400">
                              {topSuspect.symbol} (Score: {topSuspect.score.toFixed(2)})
                            </span>
                          </div>
                        ) : (
                          <span className="text-zinc-500 font-mono">—</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <VerificationBadge
                          status={latestPatch?.verification_status || "unverified"}
                        />
                      </td>

                      <td className="py-3.5 px-4 text-zinc-400 font-mono text-[11px]">
                        {formatTimeAgo(item.created_at)}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/analyses/${item.id}`}
                          className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium"
                        >
                          View
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
