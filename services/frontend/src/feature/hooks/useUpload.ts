// src/features/upload/hooks/useUpload.ts
import { useState } from "react";
import { uploadFiles } from "../../adapter/uploadAdapter";
import type { FileWithSettings } from "../../types";

export const useUpload = (onSuccess: (data: any) => void) => {
  const [files, setFiles] = useState<FileWithSettings[]>([]);

  const addFiles = (newFiles: File[]) => {
    const formatted: FileWithSettings[] = [{
      file: newFiles[0],
      preprocess: false,
    }];
    setFiles(formatted);
  };

  const removeFile = (_index: number) => {
    setFiles([]);
  };

  const togglePreprocess = (index: number) => {
    setFiles((prev) =>
      prev.map((f, i) =>
        i === index ? { ...f, preprocess: !f.preprocess } : f
      )
    );
  };

  const upload = async () => {
    if (!files.length) return;
    try {
      const data = await uploadFiles(files);
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

  return { files, addFiles, removeFile, togglePreprocess, upload };
};