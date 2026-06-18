import { useState } from "react";
import { generateScript } from "../../adapter/dataAdapter";
import type { GeneratePayload } from "../../types";

export const useData = (onSuccess?: (data: any) => void) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runDeploy = async (payload: GeneratePayload) => {
    setLoading(true);
    setError(null);

    try {
      const result = await generateScript(payload);
      onSuccess?.(result);
      return result;
    } catch (err: any) {
      console.error("Deploy error:", err);
      setError(err.message || "Error al desplegar la configuración");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { runDeploy, loading, error };
};