/**
 * @file useData.ts
 * @description Hook encargado de abstraer la llamada al endpoint de generación de código (State 2).
 */

import { useAsyncAction } from "./useAsyncAction";
import { deployDossier } from "../../adapter/dataAdapter";
import type { GeneratePayload } from "../../types";

/**
 * Encapsula la llamada a `deployDossier` con gestión de estado de carga y errores.
 * 
 * @param onSuccess - Callback invocado con el código Python generado si el deploy tiene éxito.
 * @returns Objeto con la función disparadora `runDeploy` y los estados reactivos.
 */
export const useData = (onSuccess?: (data: any) => void) => {
  const { run: runDeploy, loading, error } = useAsyncAction<GeneratePayload, any>(
    deployDossier,
    onSuccess
  );
  return { runDeploy, loading, error };
};