// src/adapters/uploadAdapter.ts
import { post } from "./xhr";
import type { FileWithSettings } from "../types";

export const uploadFiles = async (file: FileWithSettings[]) => {
  const formData = new FormData();

  const item = file[0];

  formData.append("file", item.file);
  formData.append("preprocess", String(item.preprocess));
  
  return post("/upload", formData);
};