"use client";

import React, { useRef, useState, useEffect } from "react";
import { X, Edit3, Check } from "lucide-react";

interface Props {
  urls: string[];
  onRemove: (index: number) => void;
}

export function ImagePreview({ urls, onRemove }: Props) {
  const [annotatingIdx, setAnnotatingIdx] = useState<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (annotatingIdx !== null && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      const img = new Image();
      img.src = urls[annotatingIdx];
      img.onload = () => {
        canvas.width = img.width > 600 ? 600 : img.width;
        canvas.height = (img.height / img.width) * canvas.width;
        ctx?.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
    }
  }, [annotatingIdx, urls]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    setIsDrawing(true);
    setStartPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPos || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const endX = e.clientX - rect.left;
    const endY = e.clientY - rect.top;

    const ctx = canvasRef.current.getContext("2d");
    if (ctx) {
      ctx.strokeStyle = "#ef4444";
      ctx.lineWidth = 3;
      ctx.strokeRect(startPos.x, startPos.y, endX - startPos.x, endY - startPos.y);
    }
    setIsDrawing(false);
  };

  if (urls.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {urls.map((url, idx) => (
          <div
            key={idx}
            className="group relative rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden aspect-video flex items-center justify-center"
          >
            <img src={url} alt={`Screenshot ${idx + 1}`} className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => setAnnotatingIdx(idx)}
                className="p-1.5 rounded-lg bg-zinc-800 text-zinc-200 hover:bg-zinc-700"
                title="Annotate bug region"
              >
                <Edit3 className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => onRemove(idx)}
                className="p-1.5 rounded-lg bg-rose-600/80 text-white hover:bg-rose-500"
                title="Remove image"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Lightweight Annotation Modal */}
      {annotatingIdx !== null && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-4 max-w-2xl w-full space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-300">
                Drag to draw a red box around the bug area
              </span>
              <button
                onClick={() => setAnnotatingIdx(null)}
                className="px-3 py-1 rounded-lg bg-indigo-600 text-white text-xs font-medium flex items-center gap-1"
              >
                <Check className="w-3.5 h-3.5" />
                Done
              </button>
            </div>
            <div className="border border-zinc-800 rounded-lg overflow-hidden flex justify-center bg-black">
              <canvas
                ref={canvasRef}
                onMouseDown={handleMouseDown}
                onMouseUp={handleMouseUp}
                className="cursor-crosshair max-w-full"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
