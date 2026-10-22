"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Repo } from "@/lib/types";
import { RepoPicker } from "@/components/upload/RepoPicker";
import { formatTimeAgo } from "@/lib/utils";
import { Layers, Trash2, GitBranch, FileCode, Plus, Loader2 } from "lucide-react";

export default function ReposPage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const fetchRepos = () => {
    setLoading(true);
    api
      .getRepos()
      .then(setRepos)
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchRepos();
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete repository '${name}'?`)) return;
    try {
      await api.deleteRepo(id);
      setRepos((prev) => prev.filter((r) => r.id !== id));
    } catch (err: any) {
      alert(err.message || "Failed to delete repository");
    }
  };

  const getLanguageColor = (lang: string) => {
    if (lang.includes("React") || lang.includes("JavaScript")) return "bg-amber-400";
    if (lang.includes("TypeScript")) return "bg-blue-400";
    if (lang.includes("Python")) return "bg-emerald-400";
    if (lang.includes("Java")) return "bg-rose-400";
    return "bg-zinc-500";
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            Repository Manager
          </h1>
          <p className="text-xs text-zinc-400 mt-1">
            Repositories with parsed AST symbol chunks and cached BM25 indices.
          </p>
        </div>

        <button
          onClick={() => setShowAdd(!showAdd)}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
        >
          <Plus className="w-3.5 h-3.5" />
          {showAdd ? "Close" : "Add Repository"}
        </button>
      </div>

      {showAdd && (
        <div className="mb-8 p-6 rounded-2xl border border-zinc-800 bg-zinc-950/70 backdrop-blur">
          <RepoPicker
            repos={repos}
            selectedRepoId={null}
            onSelect={() => {}}
            onRepoCreated={(r) => {
              setRepos((prev) => [r, ...prev]);
              setShowAdd(false);
            }}
          />
        </div>
      )}

      {loading ? (
        <div className="p-16 text-center text-zinc-500 flex items-center justify-center gap-2 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
          Loading repositories...
        </div>
      ) : repos.length === 0 ? (
        <div className="p-16 text-center text-zinc-500 border border-zinc-800 rounded-2xl bg-zinc-950/40">
          <Layers className="w-10 h-10 mx-auto mb-3 opacity-30 text-indigo-400" />
          <h3 className="text-sm font-semibold text-zinc-300">No repositories indexed</h3>
          <p className="text-xs text-zinc-500 mt-1">Upload a ZIP file or clone a Git URL to begin.</p>
          <button
            onClick={() => setShowAdd(true)}
            className="mt-4 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
          >
            Add Repository
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {repos.map((repo) => {
            const stats = repo.language_stats || {};
            const totalLines = Object.values(stats).reduce((a, b) => a + b, 0);

            return (
              <div
                key={repo.id}
                className="p-5 rounded-2xl border border-zinc-800 bg-zinc-950/60 backdrop-blur hover:border-zinc-700 transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <h3 className="text-sm font-bold text-zinc-100">{repo.name}</h3>
                      <div className="flex items-center gap-2 text-[11px] text-zinc-500 font-mono mt-0.5">
                        <span className="flex items-center gap-1">
                          <GitBranch className="w-3 h-3 text-indigo-400" />
                          {repo.default_branch}
                        </span>
                        {repo.commit_sha && <span>• {repo.commit_sha.slice(0, 7)}</span>}
                        <span>• Added {formatTimeAgo(repo.created_at)}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDelete(repo.id, repo.name)}
                      className="p-1.5 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                      title="Delete Repository"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Language breakdown bar */}
                  {totalLines > 0 && (
                    <div className="space-y-1.5 mb-4">
                      <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden flex">
                        {Object.entries(stats).map(([lang, lines]) => {
                          const pct = (lines / totalLines) * 100;
                          return (
                            <div
                              key={lang}
                              className={`h-full ${getLanguageColor(lang)}`}
                              style={{ width: `${pct}%` }}
                              title={`${lang}: ${lines} LOC (${pct.toFixed(1)}%)`}
                            />
                          );
                        })}
                      </div>

                      <div className="flex flex-wrap gap-2 text-[10px] text-zinc-400">
                        {Object.entries(stats).map(([lang, lines]) => (
                          <span key={lang} className="flex items-center gap-1">
                            <span className={`w-1.5 h-1.5 rounded-full ${getLanguageColor(lang)}`} />
                            <span>{lang}</span>
                            <span className="text-zinc-600">({lines} LOC)</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-zinc-800/60 flex items-center justify-between text-xs text-zinc-500 font-mono">
                  <span>Status: <span className="text-emerald-400 capitalize">{repo.index_status}</span></span>
                  <span>Source: {repo.source_type.toUpperCase()}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
