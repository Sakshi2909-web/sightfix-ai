import { create } from "zustand";

interface NewAnalysisState {
  step: number;
  selectedRepoId: string | null;
  title: string;
  description: string;
  platform: string;
  screenshots: File[];
  screenshotUrls: string[];
  video: File | null;
  logsText: string;
  logsFile: File | null;

  setStep: (step: number) => void;
  setSelectedRepoId: (id: string | null) => void;
  setTitle: (title: string) => void;
  setDescription: (desc: string) => void;
  setPlatform: (p: string) => void;
  addScreenshot: (file: File) => void;
  removeScreenshot: (index: number) => void;
  setVideo: (file: File | null) => void;
  setLogsText: (text: string) => void;
  setLogsFile: (file: File | null) => void;
  reset: () => void;
}

export const useAnalysisStore = create<NewAnalysisState>((set) => ({
  step: 1,
  selectedRepoId: null,
  title: "",
  description: "",
  platform: "web",
  screenshots: [],
  screenshotUrls: [],
  video: null,
  logsText: "",
  logsFile: null,

  setStep: (step) => set({ step }),
  setSelectedRepoId: (selectedRepoId) => set({ selectedRepoId }),
  setTitle: (title) => set({ title }),
  setDescription: (description) => set({ description }),
  setPlatform: (platform) => set({ platform }),
  addScreenshot: (file) =>
    set((state) => ({
      screenshots: [...state.screenshots, file],
      screenshotUrls: [...state.screenshotUrls, URL.createObjectURL(file)],
    })),
  removeScreenshot: (index) =>
    set((state) => {
      const newFiles = [...state.screenshots];
      const newUrls = [...state.screenshotUrls];
      newFiles.splice(index, 1);
      newUrls.splice(index, 1);
      return { screenshots: newFiles, screenshotUrls: newUrls };
    }),
  setVideo: (video) => set({ video }),
  setLogsText: (logsText) => set({ logsText }),
  setLogsFile: (logsFile) => set({ logsFile }),
  reset: () =>
    set({
      step: 1,
      selectedRepoId: null,
      title: "",
      description: "",
      platform: "web",
      screenshots: [],
      screenshotUrls: [],
      video: null,
      logsText: "",
      logsFile: null,
    }),
}));
