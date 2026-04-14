// src/features/upload/hooks/useUpload.ts
import { useState } from "react";
import { uploadFiles } from "../../../adapter/uploadAdapter";
import type { FileWithSettings } from "../types";

export const useUpload = (onSuccess: (data: any) => void) => {
  const [files, setFiles] = useState<FileWithSettings[]>([]);

  const addFiles = (newFiles: File[]) => {
    const formatted = newFiles.map((file) => ({
      file,
      preprocess: false,
    }));
    setFiles((prev) => [...prev, ...formatted]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
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
    const data = await uploadFiles(files);
    onSuccess(data);
  };

  return {
    files,
    addFiles,
    removeFile,
    togglePreprocess,
    upload,
  };
};