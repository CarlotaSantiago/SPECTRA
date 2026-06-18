/**
 * @file useAnalysis.ts
 * @description Hook encargado de abstraer la llamada al endpoint de análisis de datos (State 1).
 */

import { useAsyncAction } from "./useAsyncAction";
import { processState1 } from "../../adapter/analysisAdapter";
import type { ManifestPayload } from "../../types";

/**
 * Encapsula la llamada a `processState1` con gestión automática de estado (loading, error).
 * 
 * @param onSuccess - Callback que se ejecuta recibiendo el `DossierData` si la petición es exitosa.
 * @returns Objeto con la función disparadora `runAnalysis` y los estados reactivos `loading` y `error`.
 */
export const useAnalysis = (onSuccess?: (data: any) => void) => {
  const { run: runAnalysis, loading, error } = useAsyncAction<ManifestPayload, any>(
    processState1,
    onSuccess
  );
  return { runAnalysis, loading, error };
};