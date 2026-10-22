"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { FileCode, Loader2, AlertCircle } from "lucide-react";

// Dynamically import Monaco Editor to avoid SSR hydration issues
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

interface Props {
  repoId: string;
  filePath: string;
  highlightLines?: [number, number];
}

export function CodeViewer({ repoId, filePath, highlightLines }: Props) {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!repoId || !filePath) return;
    setLoading(true);
    setError(null);

    api
      .getRepoFile(repoId, filePath)
      .then((res) => {
        setContent(res.content);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [repoId, filePath]);

  const getLanguage = (path: string) => {
    if (path.endsWith(".jsx") || path.endsWith(".js")) return "javascript";
    if (path.endsWith(".tsx") || path.endsWith(".ts")) return "typescript";
    if (path.endsWith(".py")) return "python";
    if (path.endsWith(".json")) return "json";
    if (path.endsWith(".html")) return "html";
    if (path.endsWith(".css")) return "css";
    return "plaintext";
  };

  return (
    <div className="h-full flex flex-col border border-zinc-800 rounded-xl overflow-hidden bg-zinc-950">
      <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-900 border-b border-zinc-800 text-xs">
        <div className="flex items-center gap-2 text-zinc-300 font-mono">
          <FileCode className="w-4 h-4 text-indigo-400" />
          <span>{filePath}</span>
        </div>
        {highlightLines && (
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            Target lines: {highlightLines[0]} - {highlightLines[1]}
          </span>
        )}
      </div>

      <div className="flex-1 relative min-h-[400px]">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-zinc-950 text-zinc-500 gap-2 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
            Loading source code...
          </div>
        ) : error ? (
          <div className="absolute inset-0 flex items-center justify-center bg-zinc-950 text-rose-400 gap-2 text-xs p-4 text-center">
            <AlertCircle className="w-4 h-4" />
            Failed to load file: {error}
          </div>
        ) : (
          <Editor
            height="100%"
            theme="vs-dark"
            language={getLanguage(filePath)}
            value={content}
            options={{
              readOnly: true,
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "JetBrains Mono, monospace",
              scrollBeyondLastLine: false,
              automaticLayout: true,
              renderLineHighlight: "all",
            }}
          />
        )}
      </div>
    </div>
  );
}
