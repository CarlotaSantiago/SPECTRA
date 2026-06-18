/**
 * @file useScript.ts
 * @description Hook complejo que gestiona el estado local del editor de código y el envío
 * final del script para su ejecución o persistencia.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { editScript } from "../../adapter/dataAdapter";
import { initializeDossierConstraints } from "./useDefaultConstraints";

/**
 * Hook para la vista del editor de código (ViewScriptPage).
 * Gestiona la inicialización del código fuente, las restricciones y el despliegue final.
 * 
 * @param state - El estado inyectado a través de react-router-dom que contiene el `toonData`.
 * @param resolveSelection - Función inyectada por `useOllamaModels` para mapear el display_name al ID real del modelo.
 */
export const useScriptDeployment = (
  state: any,
  resolveSelection: (model: string) => { model: string; provider?: string }
) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const [scriptCode, setScriptCode] = useState<string>(() => {
    if (state?.script) return state.script;
    if (state?.toonData?.script) return state.toonData.script;
    if (state?.toonData?.data?.script) return state.toonData.data.script;

    return [
      "import json",
      "import os",
      "import warnings",
      "from typing import Any, Dict, List, Optional, Tuple",
      "",
      "import joblib",
      "import numpy as np",
      "import optuna",
    ].join("\n");
  });

  const [dossier] = useState<any>(() =>
    initializeDossierConstraints(state?.toonData || null)
  );

  const deployScript = async (selectedModel: string) => {
    if (!selectedModel) {
      alert("Por favor, selecciona un modelo antes de continuar.");
      return;
    }

    setLoading(true);
    const { model, provider } = resolveSelection(selectedModel);
    const payload = {
      script: scriptCode,
      model,
      ...(provider && { provider }),
    };

    try {
      const result = await editScript(payload as any);

      navigate("/results", {
        state: {
          scriptCode: result.script || result.data?.script,
          toonData: result,
        },
      });
    } catch (error) {
      console.error("Error en deployScript:", error);
      alert("No se pudo conectar con el servidor o procesar el entrenamiento.");
    } finally {
      setLoading(false);
    }
  };

  return { scriptCode, setScriptCode, dossier, loading, deployScript };
};