"use client";

import React, { useRef, useState } from "react";
import { Image as ImageIcon, Video, Upload } from "lucide-react";

interface Props {
  onImagesSelected: (files: File[]) => void;
  onVideoSelected?: (file: File) => void;
  maxFiles?: number;
}

export function Dropzone({ onImagesSelected, onVideoSelected, maxFiles = 6 }: Props) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const imgList: File[] = [];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      if (f.type.startsWith("image/")) {
        imgList.push(f);
      } else if (f.type.startsWith("video/") && onVideoSelected) {
        onVideoSelected(f);
      }
    }
    if (imgList.length > 0) {
      onImagesSelected(imgList.slice(0, maxFiles));
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`p-6 border-2 border-dashed rounded-2xl text-center cursor-pointer transition-all ${
        isDragOver
          ? "border-indigo-500 bg-indigo-950/20"
          : "border-zinc-800 hover:border-zinc-700 bg-zinc-900/40"
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,video/*"
        onChange={(e) => handleFiles(e.target.files)}
        className="hidden"
      />
      <div className="flex justify-center items-center gap-3 mb-2 text-indigo-400">
        <ImageIcon className="w-6 h-6" />
        <Video className="w-6 h-6 text-cyan-400" />
      </div>
      <p className="text-xs font-semibold text-zinc-200 mb-1">
        Drag & drop screenshots or screen recordings
      </p>
      <p className="text-[11px] text-zinc-500">
        PNG, JPG, MP4, WebM (up to {maxFiles} images or 1 video keyframe extraction)
      </p>
    </div>
  );
}
