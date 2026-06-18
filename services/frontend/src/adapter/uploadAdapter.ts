/**
 * @file uploadAdapter.ts
 * @description Capa adaptadora para gestionar el proceso de subida inicial de datasets al sistema.
 */

import { post } from "./xhr";
import type { FileWithSettings, UploadResponse } from "../types";

/**
 * Realiza la petición para subir uno o múltiples archivos al servidor.
 * Internamente convierte los datos a un objeto `FormData` (multipart/form-data) 
 * que el backend pueda parsear.
 * 
 * @param file - Un array de archivos enriquecidos con sus configuraciones de preprocesamiento.
 * @returns Una promesa que resuelve al `UploadResponse` confirmando el éxito o fallo de la subida.
 */
export const uploadFiles = async (file: FileWithSettings[]): Promise<UploadResponse> => {
  const formData = new FormData();

  // Por diseño actual de la UI y del Backend, procesamos únicamente el primer archivo enviado.
  const item = file[0];

  formData.append("file", item.file);
  formData.append("preprocess", String(item.preprocess));
  
  return post("/upload", formData);
};