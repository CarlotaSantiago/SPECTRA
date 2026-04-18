import { create } from "zustand";
import { persist } from "zustand/middleware";


interface DatasetState {
  data: any | null;
  setData: (data: any) => void;
  clear: () => void;
}


export const useDatasetStore = create<DatasetState>()(
  persist(
    (set) => ({
      data: null,
      setData: (data) => set({ data }),
      clear: () => set({ data: null }),
    }),
    {
      name: "dataset-storage",
    }
  )
);