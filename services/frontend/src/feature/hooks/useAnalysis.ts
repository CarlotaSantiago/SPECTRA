import { useState } from "react";
import { processState1 } from "../../adapter/analysisAdapter";
import type { DossierPayload } from "../types";

export const useAnalysis = (onSuccess?: (data: any) => void) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async (payload: DossierPayload) => {
    setLoading(true);
    setError(null);

    try {
      const result = await processState1(payload);
      onSuccess?.(result);
      return result;
    } catch (err: any) {
      console.error("Analysis error:", err);
      setError(err.message || "Error en análisis");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { runAnalysis, loading, error };
};