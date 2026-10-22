"use client";

import React, { useState } from "react";
import { Repo } from "@/lib/types";
import { Layers, Plus, Upload, GitBranch, Check, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

interface Props {
  repos: Repo[];
  selectedRepoId: string | null;
  onSelect: (repoId: string) => void;
  onRepoCreated: (newRepo: Repo) => void;
}

export function RepoPicker({ repos, selectedRepoId, onSelect, onRepoCreated }: Props) {
  const [mode, setMode] = useState<"select" | "upload" | "git">("select");
  const [gitUrl, setGitUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleZipUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const created = await api.createRepoZip(fd);
      onRepoCreated(created);
      onSelect(created.id);
      setMode("select");
    } catch (err: any) {
      setError(err.message || "Failed to upload zip archive");
    } finally {
      setUploading(false);
    }
  };

  const handleGitClone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gitUrl.trim()) return;
    setUploading(true);
    setError(null);
    try {
      const created = await api.createRepoGit(gitUrl, branch);
      onRepoCreated(created);
      onSelect(created.id);
      setMode("select");
      setGitUrl("");
    } catch (err: any) {
      setError(err.message || "Failed to clone repository");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Tab toggle */}
      <div className="flex gap-2 p-1 bg-zinc-900 border border-zinc-800 rounded-lg max-w-fit">
        <button
          type="button"
          onClick={() => setMode("select")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
            mode === "select" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          Select Existing ({repos.length})
        </button>
        <button
          type="button"
          onClick={() => setMode("upload")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
            mode === "upload" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          Upload ZIP
        </button>
        <button
          type="button"
          onClick={() => setMode("git")}
          className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
            mode === "git" ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"
          }`}
        >
          Git Clone
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Select Mode */}
      {mode === "select" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1">
          {repos.length === 0 ? (
            <div className="col-span-2 p-8 text-center text-zinc-500 border border-zinc-800 rounded-xl bg-zinc-900/40">
              <Layers className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">No repositories indexed yet.</p>
              <button
                onClick={() => setMode("upload")}
                className="mt-3 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium"
              >
                Upload your first repo
              </button>
            </div>
          ) : (
            repos.map((repo) => {
              const isSelected = selectedRepoId === repo.id;
              const mainLang = repo.language_stats ? Object.keys(repo.language_stats)[0] : "Code";

              return (
                <div
                  key={repo.id}
                  onClick={() => onSelect(repo.id)}
                  className={`p-3.5 rounded-xl border transition cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? "bg-indigo-950/20 border-indigo-500/60 shadow-md shadow-indigo-500/5"
                      : "bg-zinc-900/60 border-zinc-800 hover:border-zinc-700"
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-xs text-zinc-100 truncate">{repo.name}</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 font-mono">
                        {mainLang}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-zinc-500 font-mono">
                      <span>{repo.default_branch}</span>
                      {repo.commit_sha && <span>• {repo.commit_sha.slice(0, 7)}</span>}
                    </div>
                  </div>

                  <div className="flex-shrink-0">
                    {isSelected ? (
                      <div className="w-5 h-5 rounded-full bg-indigo-500 text-white flex items-center justify-center">
                        <Check className="w-3 h-3" />
                      </div>
                    ) : (
                      <div className="w-5 h-5 rounded-full border border-zinc-700" />
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Upload ZIP Mode */}
      {mode === "upload" && (
        <div className="p-8 border-2 border-dashed border-zinc-800 hover:border-indigo-500/50 rounded-2xl bg-zinc-900/40 text-center transition">
          <Upload className="w-8 h-8 mx-auto mb-2 text-indigo-400" />
          <p className="text-xs font-medium text-zinc-200 mb-1">Upload repository ZIP archive</p>
          <p className="text-[11px] text-zinc-500 mb-4">Max 50MB. Safe unzipping with zip-slip prevention.</p>
          <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition">
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? "Extracting & Indexing..." : "Choose ZIP file"}
            <input
              type="file"
              accept=".zip"
              disabled={uploading}
              onChange={handleZipUpload}
              className="hidden"
            />
          </label>
        </div>
      )}

      {/* Git Clone Mode */}
      {mode === "git" && (
        <form onSubmit={handleGitClone} className="p-4 border border-zinc-800 rounded-xl bg-zinc-900/60 space-y-3">
          <div>
            <label className="text-xs text-zinc-400 block mb-1">Git Repository URL</label>
            <input
              type="text"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/org/repo.git"
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-400 block mb-1">Branch</label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={uploading || !gitUrl.trim()}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium transition flex items-center gap-2"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
            {uploading ? "Cloning..." : "Clone & Index"}
          </button>
        </form>
      )}
    </div>
  );
}
