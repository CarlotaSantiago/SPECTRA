import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Brain, LayoutGrid, Activity, ChevronUp, ChevronDown, Code, FileText, CheckCircle } from "lucide-react";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";
import { LoadingOverlay } from "../feature/components/LoadingOverlay";

// =====================================================================
// COMPONENTE PRINCIPAL
// =====================================================================
export const ViewScriptPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const { models: ollamaModels, loading: loadingModels, resolveSelection } = useOllamaModels();
  const [selectedModel, setSelectedModel] = useState("llama3"); // Puesto por defecto para desarrollo o añade picker

  // --- CAPTURA UNIFICADA DEL SCRIPT ---
  const [scriptCode, setScriptCode] = useState<string>(() => {
    if (state?.script) return state.script;
    if (state?.toonData?.script) return state.toonData.script;
    if (state?.toonData?.data?.script) return state.toonData.data.script;
    
    return "import json\nimport os\nimport warnings\nfrom typing import Any, Dict, List, Optional, Tuple\n\nimport joblib\nimport numpy as np\nimport optuna\n";
  });

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

  if (!dossier) {
    return (
      <div style={errorStyle}>
        <h2>No se encontraron datos del análisis.</h2>
        <button onClick={() => navigate(-1)} style={backBtnStyle}>Volver</button>
      </div>
    );
  }

  const handleDeploy = async () => {
    if (!selectedModel) {
      alert("Por favor, selecciona un modelo antes de continuar.");
      return;
    }

    setLoading(true);
    const { provider } = resolveSelection(selectedModel);
    
    // Enviamos el scriptCode que está mutando el usuario en tiempo real en la columna 1
    const payload = {
      script: scriptCode, 
      ...(provider && { provider }),
    };

    try {
      console.log("payload a enviar: ", payload)
      const response = await fetch("http://localhost:8000/send-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        console.log(result)
        navigate("/results", { 
          state: { 
            scriptCode: result.script || result.data?.script,
            // O si prefieres pasarle todo el objeto que devolvió el servidor:
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
  const artifactsList = state?.artifacts || [];

  return (
    <div style={containerStyle}>
      {(loading) && <LoadingOverlay message="Entrenando modelos..." />}
      
      <div style={headerStyle}>
        <button onClick={() => navigate(-1)} style={backBtnStyle}><ArrowLeft size={18} /> Volver</button>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={handleDeploy} style={deployBtnStyle}>
            <Brain size={18} /> Iniciar Entrenamiento con Métricas
          </button>
        </div>
      </div>
        
        {/* COLUMNA 1: EDITOR DE SCRIPT PYTHON & PANEL DE ARTEFACTOS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: 'calc(100vh - 120px)' }}>
          <div style={codePanelStyle}>
            <h3 style={cardTitle}><Code size={16}/> Script de Entrenamiento Python</h3>
            <textarea
              value={scriptCode}
              onChange={(e) => setScriptCode(e.target.value)}
              style={codeEditorStyle}
              spellCheck={false}
            />
            <div style={{fontSize: '11px', color: '#666', marginTop: '5px'}}>
              * Las modificaciones en este script se enviarán directamente al backend para su ejecución.
            </div>
          </div>

          {/* Artefactos */}
          {artifactsList.length > 0 && (
            <div style={{ ...cardStyle, flex: '0 0 auto', maxHeight: '200px', overflowY: 'auto' }}>
              <h3 style={cardTitle}><FileText size={16}/> Artefactos Generados ({artifactsList.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {artifactsList.map((art: any, index: number) => (
                  <div key={index} style={artifactRowStyle}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle size={14} color="#648f8c" />
                      <span style={{ fontSize: '12px', fontWeight: '500' }}>{art.name}</span>
                    </div>
                    <span style={{ fontSize: '10px', color: '#666' }}>
                      {(art.size_bytes / 1024).toFixed(2)} KB | {art.kind}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
  );
};

// =====================================================================
// ESTILOS DE LA INTERFAZ (Se mantiene tu Layout de 3 columnas limpio)
// =====================================================================
const containerStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", height: "calc(100vh-50px)", padding: "10px", boxSizing: "border-box", overflow: "hidden", fontFamily: "sans-serif", display: "flex", flexDirection: "column"};
const headerStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" };
const codePanelStyle: React.CSSProperties = { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333", display: "flex", flexDirection: "column", flex: 1 };
const codeEditorStyle: React.CSSProperties = { flex: 1, backgroundColor: "#0b0b0b", color: "#a9dc76", border: "1px solid #222", borderRadius: "6px", padding: "12px", fontFamily: "Courier New, monospace", fontSize: "12px", lineHeight: "1.5", resize: "none", outline: "none", minHeight: "350px" };
const cardStyle: React.CSSProperties = { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333" };
const cardTitle: React.CSSProperties = { color: "#648f8c", fontSize: "14px", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px", fontWeight: "bold" };
const errorStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "20px" };
const deployBtnStyle: React.CSSProperties = { backgroundColor: "#648f8c", border: "none", color: "white", padding: "8px 16px", borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", fontWeight: "bold" };
const artifactRowStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "#151515", padding: "6px 10px", borderRadius: "6px", border: "1px solid #252525" };
const backBtnStyle: React.CSSProperties = { background: "none", border: "none", color: "#648f8c", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px"};
export default ViewScriptPage;