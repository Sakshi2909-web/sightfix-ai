import { Repo, Analysis, Patch, BugReport } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, options);
  if (!res.ok) {
    let errMessage = `API error: ${res.status} ${res.statusText}`;
    try {
      const errData = await res.json();
      if (errData.detail) errMessage = errData.detail;
      else if (errData.message) errMessage = errData.message;
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }
  if (res.status === 204) {
    return {} as T;
  }
  return res.json();
}

export const api = {
  // Repos
  getRepos: () => request<Repo[]>("/api/repos"),
  getRepo: (id: string) => request<Repo>(`/api/repos/${id}`),
  createRepoZip: (formData: FormData) =>
    request<Repo>("/api/repos", { method: "POST", body: formData }),
  createRepoGit: (git_url: string, branch: string = "main") => {
    const fd = new FormData();
    fd.append("git_url", git_url);
    fd.append("branch", branch);
    return request<Repo>("/api/repos", { method: "POST", body: fd });
  },
  deleteRepo: (id: string) =>
    request<void>(`/api/repos/${id}`, { method: "DELETE" }),
  getRepoFile: (repoId: string, path: string, start?: number, end?: number) => {
    const params = new URLSearchParams({ path });
    if (start) params.append("start", start.toString());
    if (end) params.append("end", end.toString());
    return request<{ path: string; total_lines: number; start: number; end: number; content: string }>(
      `/api/repos/${repoId}/file?${params.toString()}`
    );
  },

  // Analyses
  getAnalyses: (repoId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (repoId) params.append("repo_id", repoId);
    if (status) params.append("status", status);
    return request<Analysis[]>(`/api/analyses?${params.toString()}`);
  },
  getAnalysis: (id: string) => request<Analysis>(`/api/analyses/${id}`),
  createAnalysis: (formData: FormData) =>
    request<{ analysis_id: string; report_id: string }>("/api/analyses", {
      method: "POST",
      body: formData,
    }),
  rerunAnalysis: (id: string, weights?: Record<string, number>) =>
    request<{ status: string; message: string }>(`/api/analyses/${id}/rerun`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(weights || {}),
    }),

  // Patches
  getLatestPatch: (analysisId: string) =>
    request<Patch>(`/api/analyses/${analysisId}/patch`),
  regeneratePatch: (analysisId: string, feedback: string) =>
    request<Patch>(`/api/analyses/${analysisId}/patch/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback }),
    }),

  // Feedback
  submitFeedback: (analysisId: string, suspect_rank_correct: boolean, correct_file?: string) =>
    request<{ status: string }>(`/api/analyses/${analysisId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ suspect_rank_correct, correct_file }),
    }),

  // Health
  getHealth: () => request<Record<string, any>>("/api/health"),
};
