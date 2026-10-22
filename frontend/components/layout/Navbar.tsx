"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./ThemeToggle";
import { api } from "@/lib/api";
import { Bug, Sparkles, Layers, History, Settings, ExternalLink } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const [providerInfo, setProviderInfo] = useState<string>("mock");
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    api.getHealth().then((h) => {
      if (h.providers?.vlm) {
        setProviderInfo(h.providers.vlm);
      }
    }).catch(() => {});
  }, []);

  const links = [
    { href: "/analyze/new", label: "New Analysis", icon: Sparkles },
    { href: "/analyses", label: "History", icon: History },
    { href: "/repos", label: "Repositories", icon: Layers },
  ];

  return (
    <>
      <header className="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2.5 font-bold text-sm tracking-tight text-zinc-100">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Bug className="w-4 h-4 text-white" />
              </div>
              <span>
                SightFix <span className="text-cyan-400 font-mono text-xs">AI</span>
              </span>
            </Link>

            {/* Nav links */}
            <nav className="hidden md:flex items-center gap-1">
              {links.map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                      isActive
                        ? "bg-zinc-800 text-zinc-100 font-semibold"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right items */}
          <div className="flex items-center gap-2.5">
            {/* Active Provider Pill */}
            <div
              onClick={() => setShowSettings(true)}
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-400 cursor-pointer hover:border-zinc-700"
              title="Click to view provider & privacy settings"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Provider:</span>
              <span className="text-indigo-400 uppercase font-semibold">{providerInfo}</span>
            </div>

            <button
              onClick={() => setShowSettings(true)}
              className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200"
              title="Settings & Privacy"
            >
              <Settings className="w-4 h-4" />
            </button>

            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                <Settings className="w-4 h-4 text-indigo-400" />
                System Settings & Data Transparency
              </h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-zinc-400 hover:text-zinc-200 text-xs px-2 py-1 rounded hover:bg-zinc-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-zinc-400 block mb-1 font-medium">Configured VLM & LLM Provider</label>
                <div className="p-2.5 rounded-lg bg-zinc-900 border border-zinc-800 font-mono text-indigo-300">
                  {providerInfo} (Deterministic mock fallback active when no API keys supplied)
                </div>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1 font-medium">Data Privacy & Secret Redaction</label>
                <p className="text-zinc-400 leading-relaxed bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800">
                  All uploaded console and server logs are automatically scrubbed for API keys, Bearer tokens, passwords, and user email addresses before being transmitted to providers or stored in the database.
                </p>
              </div>

              <div>
                <label className="text-zinc-400 block mb-1 font-medium">Sandboxed Execution Safety</label>
                <p className="text-zinc-400 leading-relaxed bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800">
                  Synthesized patches are verified in isolated sandboxes with network disabled (<code className="text-indigo-400">--network none</code>), strict memory & CPU limits, and timeout protection.
                </p>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
