// src/features/upload/hooks/useUpload.ts
import { useState } from "react";
import { uploadFiles } from "../../adapter/uploadAdapter";
import type { FileWithSettings } from "../../types";

export const useUpload = (onSuccess: (data: any) => void) => {
  const [file, setFile] = useState<FileWithSettings[]>([]);

  const addFile = (newFiles: File[]) => {
    const formatted: FileWithSettings[] = [{
      file: newFiles[0],
      preprocess: false,
    }];
    setFile(formatted);
  };

  const removeFile = (_index: number) => {
    setFile([]);
  };

  const togglePreprocess = (index: number) => {
    setFile((prev) =>
      prev.map((f, i) =>
        i === index ? { ...f, preprocess: !f.preprocess } : f
      )
    );
  };

  const upload = async () => {
    if (!file.length) return;
    try {
      const data = await uploadFiles(file);
      if (data) {
        onSuccess(data);
      } else {
        // Si el adapter devuelve undefined pero no lanza error
        onSuccess({ status: "error", message: "No data received" });
      }
    } catch (error) {
      console.error("Error in hook upload:", error);
      onSuccess({ status: "error", message: "Network error" });
    }
  };

  return { file, addFile, removeFile, togglePreprocess, upload };
};