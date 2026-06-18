import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { ArrowLeft, Database, ArrowRight } from "lucide-react";
import { useAnalysis } from "../feature/hooks/useAnalysis";
import { useDatasetStore } from "../store/useDatasetStore";
import { LoadingOverlay } from "../feature/components/LoadingOverlay";
import { ColumnPicker } from "../feature/components/ColumnPicker";
import { DataTable } from "../feature/components/DataTable";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";
import { ModelPicker } from "../feature/components/ModelPicker";

// --- MINI COMPONENTES INTERNOS (Para que no falle) ---
const HeaderNav = ({ onBack }: { onBack: () => void }) => (
  <button onClick={onBack} style={backBtnStyle}>
    <ArrowLeft size={16} /> Volver
  </button>
);

const Badge = ({ text }: { text: string }) => (
  <div style={badgeStyle}>{text}</div>
);

const ActionButton = ({ loading, onClick, label }: { loading: boolean, onClick: () => void, label: string }) => (
  <button onClick={onClick} disabled={loading} style={mainBtnStyle}>
    {label} <ArrowRight size={20} />
  </button>
);
  
// --- PÁGINA PRINCIPAL ---
const DataConfigPage = () => {
  const navigate = useNavigate();
  const data = useDatasetStore((s) => s.data);
  const { models: ollamaModels, loading: loadingModels } = useOllamaModels();

  // 1. Estados
  const [selectedModel, setSelectedModel] = useState("");
  const [visibleColumns, setVisibleColumns] = useState<string[]>(["descrip", "edad", "datosclini", "sospechadiag", "especialidad", "sala", "prioridad"]); // () => data?.columnas.slice(0, 5) ||  Inicializamos con las primeras 5 columnas
  const [showColumnPicker, setShowColumnPicker] = useState(false);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [roles, setRoles] = useState<Record<string, 'feature' | 'target' | 'none'>>({});
  const [blindadas, setBlindadas] = useState<Record<string, boolean>>({});

  const { runAnalysis, loading } = useAnalysis((toonData) => {
    console.log("Resultados Etapa 1:", toonData);
    navigate("/view-data", { state: { toonData } });
  });

  if (!data) return <div style={{ color: "white", padding: "20px" }}>No hay datos.</div>;

  // 2. Lógica
  const cycleRole = (col: string) => {
    setRoles(prev => {
      const current = prev[col] || 'none';
      if (current === 'none') return { ...prev, [col]: 'feature' };
      if (current === 'feature') return { ...prev, [col]: 'target' };
      return { ...prev, [col]: 'none' };
    });
  };

  const toggleColumnVisibility = (col: string) => {
    setVisibleColumns(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    );
  };

  const toggleBlindar = (e: React.MouseEvent, col: string) => {
    e.stopPropagation();
    setBlindadas(p => ({ ...p, [col]: !p[col] }));
  };

  const handleNextStep = async () => {
    const selectedTargets = Object.keys(roles).filter(k => roles[k] === 'target');
    const selectedFeatures = Object.keys(roles).filter(k => roles[k] === 'feature');
    if (selectedTargets.length === 0) {
      alert("Debes seleccionar al menos una columna como TARGET.");
      return;
    }

    if (selectedFeatures.length === 0) {
      alert("Debes seleccionar al menos una columna como FEATURE.");
      return;
    }

    if (!selectedModel) {
      alert("Por favor, selecciona un modelo de IA para el análisis.");
      return;
    }

    const manifest = {
      n_rows: data.n_rows,
      path: data.path,
      features: selectedFeatures,
      targets: selectedTargets,
      shielded: Object.keys(blindadas).filter(k => blindadas[k] && roles[k] === 'feature'),
      model: selectedModel,
      execution_mode: "auto",
      search_config: {
        search_strategy: "auto",
        max_iter: 50,
        max_combinations: 200,
        cv_folds: 10,
        timeout_minutes: 30
      }
    };

    try {
      await runAnalysis(manifest);
    } catch {
      alert("Error al procesar el análisis.");
    }
  };

  return (
    <div style={containerStyle}>
      {(loading || loadingModels) && <LoadingOverlay message={loadingModels ? "Cargando modelos de IA..." : "Analizando dataset..."} />}
    
      <HeaderNav onBack={() => navigate(-1)} />

      <div style={topControlsRow}>
        <h2 style={titleStyle}>
          <Database size={20} /> Configuración de Roles
        </h2>
        
        <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-end', 
            alignItems: 'center',
            gap: '12px' 
        }}>
          {/* --- SELECTOR DE MODELO --- */}
          <div style={{ display: 'flex', gap: '10px' }}>
          <ModelPicker 
            allModels={ollamaModels}
            selectedModel={selectedModel}
            isOpen={showModelPicker} // Necesitas un nuevo useState [showModelPicker, setShowModelPicker]
            onToggleOpen={() => setShowModelPicker(!showModelPicker)}
            onSelectModel={setSelectedModel}
          />
          <ColumnPicker 
            allColumns={data.columnas}
            visibleColumns={visibleColumns}
            isOpen={showColumnPicker}
            onToggleOpen={() => setShowColumnPicker(!showColumnPicker)}
            onToggleColumn={toggleColumnVisibility}
          />
          </div>
          <Badge text={`Inferencia del Datasets= ${data.n_rows}`} />
        </div>
      </div>

      <DataTable 
        filePath={data.path}
        allColumns={data.columnas}
        visibleColumns={visibleColumns}
        roles={roles}
        blindadas={blindadas}
        onCycleRole={cycleRole}
        onToggleBlindar={toggleBlindar}
      />

      <ActionButton 
        loading={loading} 
        onClick={handleNextStep} 
        label={loading ? "Procesando..." : "Confirmar Selección y Avanzar"} 
      />
      <footer style={{ marginTop: "2px", fontSize: "12px", color: "#888", textAlign: "center" }}>
          Selección de roles: Dossier Inicial (Features/Targets)
        </footer>
    </div>
  );
};

// --- ESTILOS (Asegúrate de que DataTable y ColumnPicker acepten estas props) ---
const selectStyle: React.CSSProperties = {
  backgroundColor: "#1e1e1e",
  color: "#648f8c",
  border: "1px solid #648f8c33",
  padding: "8px 12px",
  borderRadius: "8px",
  outline: "none",
  cursor: "pointer",
  fontWeight: "bold"
};

const containerStyle: React.CSSProperties = {
  display: "flex", 
  flexDirection: "column", 
  height: "calc(100vh - 47px)",
  padding: "20px", 
  backgroundColor: "#121212", 
  color: "white",
  boxSizing: "border-box", 
  overflow: "hidden"
};

const topControlsRow: React.CSSProperties = {
  display: "flex", justifyContent: "space-between",
  alignItems: "center", marginBottom: "20px", flexShrink: 0
};

const titleStyle: React.CSSProperties = {
  color: "#648f8c", margin: 0, display: "flex",
  alignItems: "center", gap: "10px", fontSize: "1.2rem"
};

const backBtnStyle: React.CSSProperties = {
  background: "none", border: "none", color: "#648f8c",
  display: "flex", alignItems: "center", gap: "5px",
  cursor: "pointer", marginBottom: "15px", width: "fit-content", flexShrink: 0
};

const mainBtnStyle: React.CSSProperties = {
  marginTop: "10px", padding: " 10px 14px", borderRadius: "10px",
  border: "none", backgroundColor: "#648f8c", color: "white",
  fontSize: "15px", fontWeight: "bold", cursor: "pointer",
  display: "flex", justifyContent: "center", alignItems: "center", gap: "10px", flexShrink: 0
};

const badgeStyle: React.CSSProperties = {
  backgroundColor: "#648f8c33", padding: "6px 15px", borderRadius: "20px",
  color: "#648f8c", fontSize: "13px", border: "1px solid #648f8c33", fontWeight: "bold"
};

export default DataConfigPage;