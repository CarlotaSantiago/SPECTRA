// feature/hooks/useScriptDeployment.ts
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateScript } from "../../adapter/dataAdapter";

export const useScriptDeployment = (state: any, resolveSelection: (model: string) => any) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  // Inicialización inteligente y perezosa del script
  const [scriptCode, setScriptCode] = useState<string>(() => {
    if (state?.script) return state.script;
    if (state?.toonData?.script) return state.toonData.script;
    if (state?.toonData?.data?.script) return state.toonData.data.script;
    
    return "import json\nimport os\nimport warnings\nfrom typing import Any, Dict, List, Optional, Tuple\n\nimport joblib\nimport numpy as np\nimport optuna\n";
  });

  // Inicialización inteligente de restricciones
  const [dossier] = useState<any>(() => {
    const base = state?.toonData || null;
    if (base && base.data && !base.data.user_constraints) {
      base.data.user_constraints = {
        cv_strategy: { type: "StratifiedKFold", folds: 1 },
        feature_selection_threshold: 0.05,
        allow_ensembles: true,
        optimization_priority: ["Performance", "Interpretability"],
        model_selection: {
          mode: "AUTONOMOUS_COMPETITION",
          libraries: ["scikit-learn", "xgboost", "lightgbm"]
        },
        tuning_strategy: { search_type: "Bayesian_Optimization", max_trials: 2, timeout: 60 }
      };
    }
    return base;
  });

  const deployScript = async (selectedModel: string) => {
    if (!selectedModel) {
      alert("Por favor, selecciona un modelo antes de continuar.");
      return;
    }

    setLoading(true);
    const { provider } = resolveSelection(selectedModel);
    
    const payload = {
      script: scriptCode, 
      ...(provider && { provider }),
    };

    try {
        const response = await generateScript(payload)

      if (response.ok) {
        const result = await response.json();
        navigate("/results", { 
          state: { 
            scriptCode: result.script || result.data?.script,
            toonData: result 
          } 
        });
      } else {
        throw new Error("Error en la respuesta del servidor");
      }
    } catch (error) {
      console.error(error);
      alert("No se pudo conectar con el servidor o procesar el entrenamiento.");
    } finally {
      setLoading(false);
    }
  };

  return {
    scriptCode,
    setScriptCode,
    dossier,
    loading,
    deployScript
  };
};