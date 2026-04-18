import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Database, ArrowRight } from "lucide-react";
import { useAnalysis } from "../feature/hooks/useAnalysis";
import { useDatasetStore } from "../store/useDatasetStore";
import { LoadingOverlay } from "../feature/components/LoadingOverlay";
import { ColumnPicker } from "../feature/components/ColumnPicker";
import { DataTable } from "../feature/components/DataTable";



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

  // 1. Estados
  const [visibleColumns, setVisibleColumns] = useState<string[]>(["idbuzon", "descrip", "edad", "servpeti", "desprest", "observ", "datosclini", "sospechadiag"]);
  const [showColumnPicker, setShowColumnPicker] = useState(false);
  const [roles, setRoles] = useState<Record<string, 'feature' | 'target' | 'none'>>({});
  const [blindadas, setBlindadas] = useState<Record<string, boolean>>({});

  const { runAnalysis, loading } = useAnalysis((toonData) => {
    console.log("Resultados Etapa 1:", toonData);
    // navigate("/semantic-analysis", { state: { toonData } });
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
    if (selectedTargets.length === 0) {
      alert("Debes seleccionar al menos una columna como TARGET.");
      return;
    }

    const dossier = {
      n_rows: data.n_rows,
      path: data.path,
      features: Object.keys(roles).filter(k => roles[k] === 'feature'),
      targets: selectedTargets,
      mandatory: Object.keys(blindadas).filter(k => blindadas[k] && roles[k] === 'feature')
    };

    try {
      await runAnalysis(dossier);
    } catch {
      alert("Error al procesar el análisis.");
    }
  };

  return (
    <div style={containerStyle}>
      {loading && <LoadingOverlay message="Analizando dataset..." />}
      
      <HeaderNav onBack={() => navigate(-1)} />

      <div style={topControlsRow}>
        <h2 style={titleStyle}>
          <Database size={20} /> Configuración de Roles
        </h2>
        
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <ColumnPicker 
            allColumns={data.columnas}
            visibleColumns={visibleColumns}
            isOpen={showColumnPicker}
            onToggleOpen={() => setShowColumnPicker(!showColumnPicker)}
            onToggleColumn={toggleColumnVisibility}
          />
          <Badge text={`N = ${data.n_rows}`} />
        </div>
      </div>

      <DataTable 
        previewData={data.preview}
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
    </div>
  );
};

// --- ESTILOS (Asegúrate de que DataTable y ColumnPicker acepten estas props) ---

const containerStyle: React.CSSProperties = {
  display: "flex", flexDirection: "column", height: "100vh",
  padding: "20px", backgroundColor: "#121212", color: "white",
  boxSizing: "border-box", overflow: "hidden"
};

const topControlsRow: React.CSSProperties = {
  display: "flex", justifyContent: "space-between",
  alignItems: "center", marginBottom: "20px"
};

const titleStyle: React.CSSProperties = {
  color: "#648f8c", margin: 0, display: "flex",
  alignItems: "center", gap: "10px", fontSize: "1.2rem"
};

const backBtnStyle: React.CSSProperties = {
  background: "none", border: "none", color: "#648f8c",
  display: "flex", alignItems: "center", gap: "5px",
  cursor: "pointer", marginBottom: "15px", width: "fit-content"
};

const mainBtnStyle: React.CSSProperties = {
  marginTop: "15px", padding: "14px", borderRadius: "10px",
  border: "none", backgroundColor: "#648f8c", color: "white",
  fontSize: "15px", fontWeight: "bold", cursor: "pointer",
  display: "flex", justifyContent: "center", alignItems: "center", gap: "10px"
};

const badgeStyle: React.CSSProperties = {
  backgroundColor: "#648f8c33", padding: "6px 15px", borderRadius: "20px",
  color: "#648f8c", fontSize: "13px", border: "1px solid #648f8c33", fontWeight: "bold"
};

export default DataConfigPage;