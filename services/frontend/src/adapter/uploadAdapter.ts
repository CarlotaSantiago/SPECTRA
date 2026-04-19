// src/adapters/uploadAdapter.ts
import { post } from "./xhr";
import type { FileWithSettings } from "../types";

export const uploadFiles = async (files: FileWithSettings[]) => {
  const formData = new FormData();

  files.forEach((item, index) => {
    formData.append("files", item.file);
    formData.append(`preprocess_${index}`, String(item.preprocess));
  });

  const indices = files
    .map((f, i) => (f.preprocess ? i : null))
    .filter((i) => i !== null);

  formData.append("indices_to_preprocess", JSON.stringify(indices));

  return post("/upload", formData);
};