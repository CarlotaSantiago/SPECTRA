import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Brain } from "lucide-react";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";
import { LoadingOverlay } from "../feature/components/LoadingOverlay";
import { useScriptDeployment } from "../feature/hooks/useScript"; // Asegúrate de apuntar al hook correcto
import { ScriptEditor } from "../feature/components/ScriptEditor";
import { ArtifactsList } from "../feature/components/ArtifactsList";

export const ViewScriptPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { resolveSelection } = useOllamaModels();
  
  // 1. Usamos tu hook personalizado para abstraer estados y fetch
  const { 
    scriptCode, 
    setScriptCode, 
    dossier, 
    loading, 
    deployScript 
  } = useScriptDeployment(state, resolveSelection);

  const selectedModel = "llama3"; // Si decides implementar un picker, este valor vendría de un estado local.
  const artifactsList = state?.artifacts || [];

  // 2. Control de errores basado en los datos procesados por el hook
  if (!dossier) {
    return (
      <div style={styles.errorStyle}>
        <h2>No se encontraron datos del análisis.</h2>
        <button onClick={() => navigate(-1)} style={styles.backBtnStyle}>Volver</button>
      </div>
    );
  }

  return (
    <div style={styles.containerStyle}>
      {loading && <LoadingOverlay message="Entrenando modelos..." />}
      
      {/* HEADER */}
      <div style={styles.headerStyle}>
        <button onClick={() => navigate(-1)} style={styles.backBtnStyle}>
          <ArrowLeft size={18} /> Volver
        </button>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button onClick={() => deployScript(selectedModel)} style={styles.deployBtnStyle}>
            <Brain size={18} /> Iniciar Entrenamiento con Métricas
          </button>
        </div>
      </div>
        
      {/* CONTENIDO PRINCIPAL */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: 'calc(100vh - 120px)' }}>
        
        {/* Usamos el Editor Abstraído */}
        <ScriptEditor 
          code={scriptCode} 
          onChange={setScriptCode} 
        />

        {/* Usamos la Lista de Artefactos Abstraída */}
        <ArtifactsList 
          artifacts={artifactsList} 
        />
        
      </div>
    </div>
  );
};

// =====================================================================
// ESTILOS DE LA INTERFAZ (Limpios y agrupados)
// =====================================================================
const styles: Record<string, React.CSSProperties> = {
  containerStyle: { backgroundColor: "#121212", color: "white", height: "calc(100vh - 50px)", padding: "10px", boxSizing: "border-box", overflow: "hidden", fontFamily: "sans-serif", display: "flex", flexDirection: "column" },
  headerStyle: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" },
  errorStyle: { backgroundColor: "#121212", color: "white", minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "20px" },
  deployBtnStyle: { backgroundColor: "#648f8c", border: "none", color: "white", padding: "8px 16px", borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", fontWeight: "bold" },
  backBtnStyle: { background: "none", border: "none", color: "#648f8c", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }
};

export default ViewScriptPage;