/**
 * @file useAsyncAction.ts
 * @description Hook genérico para estandarizar el consumo de endpoints asíncronos.
 * Maneja internamente los estados reactivos de carga (loading) y captura de errores.
 */

import { useState } from "react";

export const useAsyncAction = <TArgs, TResult>(
  action: (args: TArgs) => Promise<TResult>,
  onSuccess?: (data: TResult) => void
) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (args: TArgs): Promise<TResult> => {
    setLoading(true);
    setError(null);
    try {
      const result = await action(args);
      onSuccess?.(result);
      return result;
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Error desconocido";
      console.error("useAsyncAction error:", err);
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { run, loading, error };
};
