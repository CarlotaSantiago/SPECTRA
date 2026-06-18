/**
 * @file useDatasetStore.ts
 * @description Manejador de estado global utilizando Zustand. 
 * Se encarga de persistir la información del dataset recién subido a través de la sesión del usuario.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UploadResponse } from "../types";

/**
 * Interfaz del estado del almacén de datos (Store).
 */
interface DatasetState {
  /** Datos devueltos por el backend tras subir el CSV (estado, columnas detectadas, etc.) */
  data: UploadResponse | null;
  /** Función para actualizar el estado del dataset (por ejemplo, tras una subida exitosa) */
  setData: (data: UploadResponse) => void;
  /** Función para limpiar el estado, forzando al usuario a empezar de nuevo */
  clear: () => void;
}

/**
 * Hook global `useDatasetStore` que provee acceso reactivo al estado del dataset actual.
 * Utiliza el middleware `persist` para almacenar la información en `localStorage` 
 * bajo la clave "dataset-storage", previniendo pérdida de progreso al recargar la página.
 */
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