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

  const [dossier] = useState<any>(() => {
    // Si viene anidado desde model_router (body["dossier"]["data"])
    const nestedData = state?.toonData?.dossier?.data;
    // O si ya está en la raíz
    const baseData = state?.toonData?.data ? state.toonData : state?.toonData;
    const target = nestedData || baseData || null;
    
    // Lo envolvemos en un objeto "data" si no lo tiene, o devolvemos la estructura inicializada
    const initialized = initializeDossierConstraints(target);
    // ViewScriptPage espera leer dossier?.user_constraints o dossier?.data?.user_constraints
    // Vamos a asegurar que devolvemos el objeto que contiene user_constraints directamente, 
    // o el objeto data si está anidado.
    return initialized?.data || initialized;
  });

  const deployScript = async (selectedModel: string) => {

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