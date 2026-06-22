/**
 * @file ViewScriptPage.tsx
 * @description Cuarta etapa del pipeline. Muestra el editor de código 
 * permitiendo auditar y modificar el código generado antes de su ejecución física.
 * El usuario puede además configurar los parámetros de entrenamiento (CV, trials,
 * timeout) antes de lanzar el trabajo, que se inyectan automáticamente en el script.
 */

import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Brain, Save, Activity, LayoutGrid } from "lucide-react";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";
import { LoadingOverlay } from "../feature/components/LoadingOverlay";
import { useScriptDeployment } from "../feature/hooks/useScript";
import { ScriptEditor } from "../feature/components/ScriptEditor";
import { ArtifactsList } from "../feature/components/ArtifactsList";


/**
 * Renderiza un entorno de edición simple basado en texto para el script Python.
 * Renderiza un entorno de edición del script Python con una barra lateral de
 * resumen de entrenamiento. La lógica asíncrona se delega al hook
 * `useScriptDeployment`.
 */

export const ViewScriptPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { resolveSelection } = useOllamaModels();
  const [selectedModel] = useState("true");
  
  const {
    scriptCode,
    setScriptCode,
    dossier,
    loading,
    deployScript,
  } = useScriptDeployment(state, resolveSelection);

  const artifactsList = state?.artifacts || [];

  /**
   * Lanza el despliegue pasando el script actual para ejecutarlo en el backend.
   */
  const handleDeploy = () => {
    deployScript(selectedModel);
  };

  if (!dossier) {
    return (
      <div style={styles.errorStyle}>
        <h2>No se encontraron datos del análisis.</h2>
        <button onClick={() => navigate(-1)} style={styles.backBtnStyle}>
          Volver
        </button>
      </div>
    );
  }
  console.log(dossier)

  return (
    <div style={styles.containerStyle}>
      {(loading) && <LoadingOverlay message="Entrenando modelos..." />}
      
      {/* HEADER */}
      <div style={styles.headerStyle}>
        <button onClick={() => navigate(-1)} style={styles.backBtnStyle}>
          <ArrowLeft size={18} /> Volver
        </button>
        <button onClick={handleDeploy} style={styles.deployBtnStyle}>
          <Brain size={18} /> Iniciar Entrenamiento
        </button>
      </div>
        
      {/* CONTENIDO PRINCIPAL — editor a la izquierda, sidebar a la derecha */}
      <div style={styles.mainLayoutStyle}>
        {/* COLUMNA IZQUIERDA: editor + artefactos */}
        <div style={styles.editorColumnStyle}>
          <ScriptEditor code={scriptCode} onChange={setScriptCode} />
          <ArtifactsList artifacts={artifactsList} />
        </div>
        {/* COLUMNA DERECHA: parámetros de entrenamiento */}
        <aside style={styles.sidebarStyle}>
          <h2 style={styles.sectionTitleStyle}>
            <Save size={18} /> Parámetros de Entrenamiento
          </h2>
          {/* CARD: Resumen de configuración */}
          <section style={styles.cardStyle}>
            <h3 style={styles.cardTitleStyle}>
              <LayoutGrid size={16} /> Resumen de Ejecución
            </h3>
            <div style={styles.summaryRowStyle}>
              <span style={styles.labelStyle}>Folds CV:</span>
              <span style={styles.valueBadgeStyle}>{dossier?.user_constraints?.cv_strategy?.folds || 5}</span>
            </div>
            <div style={styles.summaryRowStyle}>
              <span style={styles.labelStyle}>Max Trials:</span>
              <span style={styles.valueBadgeStyle}>{dossier?.user_constraints?.tuning_strategy?.max_trials || 50}</span>
            </div>
            <div style={styles.summaryRowStyle}>
              <span style={styles.labelStyle}>Timeout:</span>
              <span style={styles.valueBadgeStyle}>{dossier?.user_constraints?.tuning_strategy?.timeout || 30} min</span>
            </div>
          </section>
        </aside>
        
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  containerStyle: {
    backgroundColor: "#121212",
    color: "white",
    height: "calc(100vh - 50px)",
    padding: "10px",
    boxSizing: "border-box",
    overflow: "auto",
    fontFamily: "sans-serif",
    display: "flex",
    flexDirection: "column",
  },
  headerStyle: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },
  mainLayoutStyle: {
    display: "grid",
    gridTemplateColumns: "1fr 280px",
    gap: "16px",
    flex: 1,
    overflow: "hidden",
  },
  editorColumnStyle: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    overflow: "hidden",
  },
  sidebarStyle: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    overflowY: "auto",
  },
  sectionTitleStyle: {
    color: "#fff",
    fontSize: "1rem",
    margin: 0,
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontWeight: 600,
  },
  cardStyle: {
    backgroundColor: "#1e1e1e",
    padding: "14px",
    borderRadius: "12px",
    border: "1px solid #333",
  },
  cardTitleStyle: {
    color: "#648f8c",
    fontSize: "13px",
    marginTop: 0,
    marginBottom: "12px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  labelStyle: {
    display: "block",
    fontSize: "11px",
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
    color: "#648f8c",
    fontWeight: "bold",
    marginBottom: "4px",
    marginTop: "8px",
  },
  rangeStyle: {
    width: "100%",
    accentColor: "#648f8c",
  },
  infoRowStyle: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "2px",
  },
  hintStyle: {
    fontSize: "10px",
    color: "#666",
    marginTop: "6px",
    display: "block",
  },
  twoColGridStyle: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "10px",
    marginTop: "4px",
  },
  numberInputStyle: {
    width: "100%",
    backgroundColor: "#121212",
    border: "1px solid #444",
    color: "#648f8c",
    borderRadius: "6px",
    padding: "6px 8px",
    fontSize: "13px",
    outline: "none",
    boxSizing: "border-box" as const,
    marginTop: "4px",
  },
  summaryRowStyle: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "8px",
  },
  valueBadgeStyle: {
    backgroundColor: "#1a3330",
    color: "#648f8c",
    borderRadius: "6px",
    padding: "2px 10px",
    fontSize: "13px",
    fontWeight: "bold",
    border: "1px solid #648f8c",
  },
  errorStyle: { backgroundColor: "#121212", color: "white", minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "20px",},
  deployBtnStyle: { backgroundColor: "#648f8c", border: "none", color: "white", padding: "8px 16px", borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", fontWeight: "bold",},
  backBtnStyle: { background: "none", border: "none", color: "#648f8c", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "14px",},
};

export default ViewScriptPage;