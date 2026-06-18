/**
 * @file useUpload.ts
 * @description Hook encargado de la lógica local de los archivos seleccionados 
 * y su subida al backend.
 */

import { useState } from "react";
import { uploadFiles } from "../../adapter/uploadAdapter";
import type { FileWithSettings } from "../../types";

/**
 * Gestiona el estado de los archivos preparados para subir.
 * 
 * @param onSuccess - Callback ejecutado con la respuesta de la subida (exitosa o error).
 * @returns Funciones y estado para añadir, remover y subir archivos.
 */
export const useUpload = (onSuccess: (data: any) => void) => {
  const [file, setFile] = useState<FileWithSettings[]>([]);

  /**
   * Añade nuevos archivos al estado. Actualmente soporta un único archivo.
   */
  const addFile = (newFiles: File[]) => {
    const formatted: FileWithSettings[] = [{
      file: newFiles[0],
      preprocess: false,
    }];
    setFile(formatted);
  };

  /** Remueve el archivo seleccionado */
  const removeFile = (_index: number) => {
    setFile([]);
  };

  /** Alterna la bandera de preprocesamiento para el archivo indicado */
  const togglePreprocess = (index: number) => {
    setFile((prev) =>
      prev.map((f, i) =>
        i === index ? { ...f, preprocess: !f.preprocess } : f
      )
    );
  };

  /** Desencadena la subida física del archivo delegando en el adapter */
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