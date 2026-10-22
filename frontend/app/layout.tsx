import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "SightFix AI — Multimodal Bug Understanding & Repair Intelligence",
  description:
    "Correlate visual UI symptoms, runtime stack traces, and repository AST to localize bugs and generate verified patches.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased min-h-screen flex flex-col selection:bg-indigo-500/30 selection:text-indigo-200">
        <Providers>
          <Navbar />
          <main className="flex-1">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
