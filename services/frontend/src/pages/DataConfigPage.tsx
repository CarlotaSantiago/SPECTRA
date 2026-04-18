import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ShieldCheck, Database, ArrowRight, Settings2, Check } from "lucide-react";
import axios from "axios";
import { LoadingOverlay } from "../feature/upload/components/LoadingOverlay"; // Importamos el nuevo componente


const DataConfigPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const data = location.state?.data;

  // 1. Configuración de columnas visibles
  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    data?.columnas?.slice(0, 8) || []
  );
  const [showColumnPicker, setShowColumnPicker] = useState(false);

  // 2. Estados de Roles y Blindaje
  const [roles, setRoles] = useState<Record<string, 'feature' | 'target' | 'none'>>({});
  const [blindadas, setBlindadas] = useState<Record<string, boolean>>({});

  if (!data) return <div style={{ padding: "50px", textAlign: "center", color: "white" }}>No hay datos.</div>;

  // Lógica de rotación de roles (Clic en cabecera)
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
    e.stopPropagation(); // Evita que el clic en el escudo active el cycleRole
    setBlindadas(p => ({ ...p, [col]: !p[col] }));
  };

  const [isProcessing, setIsProcessing] = useState(false);

const handleNextStep = async () => {
  const selectedTargets = Object.keys(roles).filter(k => roles[k] === 'target');
  
  if (selectedTargets.length === 0) {
    alert("Debes seleccionar al menos una columna como TARGET para calcular la relevancia.");
    return;
  }
  setIsProcessing(true); // Bloqueamos la UI o mostramos loader
  
  console.log(data.n_rows);
  console.log(data.path);
  console.log(data);

  const dossier = {
    n_rows: data.n_rows,        // Asegúrate de que se llame n_rows
    path: data.path,
    features: Object.keys(roles).filter(k => roles[k] === 'feature'),
    targets: Object.keys(roles).filter(k => roles[k] === 'target'),
    mandatory: Object.keys(blindadas).filter(k => blindadas[k] && roles[k] === 'feature')
  };

  try {
    // Esta llamada dispara el script de Python (Etapa 1)
    const response = await axios.post("http://localhost:8000/process-state-1", dossier);

    // El backend te devolverá el TOON (los resultados de los cálculos y la muestra estratificada)
    const toonData = response.data; 

    // Navegamos a la siguiente pantalla pasando los resultados del análisis matemático
    // navigate("/semantic-analysis", { state: { toonData } });

    console.log("Resultados de Etapa 1 (TOON):", toonData);
  } catch (err) {
    console.error("Error en Etapa 1:", err);
    alert("Error al procesar el análisis matemático.");
  } finally {
    setIsProcessing(false);
  }
};

  // Estilo dinámico para las cabeceras interactivas
  const getHeaderStyle = (col: string): React.CSSProperties => {
    const role = roles[col] || 'none';
    let border = "#444";
    let bg = "#222";

    if (role === 'feature') { border = "#3b82f6"; bg = "#2c2c2c"; }
    if (role === 'target') { border = "#10b981"; bg = "#2c2c2c"; }

    return {
      padding: "12px 10px",
      backgroundColor: bg,
      borderBottom: `3px solid ${border}`,
      cursor: "pointer",
      transition: "all 0.2s ease",
      textAlign: "left",
      minWidth: "150px",
      position: "sticky",
      top: 0,
      zIndex: 10
    };
  };

  return (
    <div style={containerStyle}>
      {isProcessing && <LoadingOverlay />}
      {/* BOTÓN VOLVER */}
      <button
        onClick={() => navigate(-1)}
        style={{ background: "none", border: "none", color: "#648f8c", display: "flex", alignItems: "center", gap: "5px", cursor: "pointer", marginBottom: "15px", width: "fit-content" }}
      >
        <ArrowRight size={16} style={{ transform: "rotate(180deg)" }} /> Volver
      </button>

      {/* HEADER SUPERIOR */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 style={{ color: "#648f8c", margin: 0, display: "flex", alignItems: "center", gap: "10px", fontSize: "1.2rem" }}>
          <Database size={20} /> Configuración de Roles
        </h2>
        
        <div style={{ display: "flex", gap: "12px", alignItems: "center", position: "relative" }}>
          <button
            onClick={() => setShowColumnPicker(!showColumnPicker)}
            style={visibilityBtnStyle(showColumnPicker)}
          >
            <Settings2 size={18} /> Ver/Ocultar Columnas
          </button>
          
          <div style={badgeStyle}>N = {data.n_total}</div>

          {/* DROPDOWN DE COLUMNAS */}
          {showColumnPicker && (
            <div style={columnPickerDropdown}>
              <div style={{ padding: "8px", fontSize: "10px", color: "#666", fontWeight: "bold", borderBottom: "1px solid #333" }}>MOSTRAR COLUMNAS</div>
              <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                {data.columnas.map((col: string) => (
                  <div 
                    key={col} 
                    onClick={() => toggleColumnVisibility(col)} 
                    style={dropdownItemStyle(visibleColumns.includes(col))}
                  >
                    {visibleColumns.includes(col) ? <Check size={12} /> : <div style={{ width: 12 }} />}
                    {col}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CONTENEDOR DE LA TABLA (Ocupa el resto de la pantalla) */}
      <div style={tableWrapper}>
        <table style={{ width: "100%", tableLayout: "fixed", borderCollapse: "separate", borderSpacing: 0 }}>
          <thead>
            <tr>
              {data.columnas.filter((c: string) => visibleColumns.includes(c)).map((col: string) => (
                <th key={col} style={getHeaderStyle(col)} onClick={() => cycleRole(col)}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", overflow: "hidden" }}>
                    <span style={{ fontSize: "8px", color: roles[col] ? "inherit" : "#666", textTransform: "uppercase", fontWeight: "bold" }}>
                      {roles[col] || 'OFF'}
                    </span>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "4px" }}>
                      <span style={colNameStyle}>
                        {col}
                      </span>
                      {roles[col] === 'feature' && (
                        <ShieldCheck 
                          size={14} 
                          onClick={(e) => toggleBlindar(e, col)}
                          style={{ color: blindadas[col] ? "#ef4444" : "#6c6c6c", flexShrink: 0 }} 
                        />
                      )}
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.preview.map((row: any, i: number) => (
              <tr key={i}>
                {data.columnas.filter((c: string) => visibleColumns.includes(c)).map((col: string) => (
                  <td key={col} style={previewTdStyle}>
                    {row[col]?.toString().substring(0, 80)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* BOTÓN DE ACCIÓN FINAL */}
      <button onClick={handleNextStep} style={mainBtnStyle}>
        Confirmar Selección y Avanzar <ArrowRight size={20} />
        {isProcessing ? "Procesando..." : "Lanzar Documentos"}
      </button>
    </div>
  );
};

// --- ESTILOS ---

const containerStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  height: "100vh",
  padding: "20px",
  backgroundColor: "#121212",
  color: "white",
  boxSizing: "border-box",
  overflow: "hidden"
};

const tableWrapper: React.CSSProperties = {
  flexGrow: 1,
  overflowY: "auto",
  overflowX: "hidden", 
  borderRadius: "12px",
  border: "1px solid #333",
  background: "#1a1a1a",
  width: "100%"
};

const colNameStyle: React.CSSProperties = {
  color: "white", 
  fontSize: "11px", 
  whiteSpace: "nowrap", 
  overflow: "hidden", 
  textOverflow: "ellipsis" 
};

const previewTdStyle: React.CSSProperties = {
  padding: "10px",
  borderBottom: "1px solid #252525",
  borderRight: "1px solid #252525",
  fontSize: "11px",
  color: "#888",
  wordBreak: "break-word",
  whiteSpace: "normal" as any, 
  verticalAlign: "top",
  lineHeight: "1.4"
};

const mainBtnStyle: React.CSSProperties = {
  marginTop: "15px",
  padding: "14px",
  borderRadius: "10px",
  border: "none",
  backgroundColor: "#648f8c",
  color: "white",
  fontSize: "15px",
  fontWeight: "bold",
  cursor: "pointer",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  gap: "10px"
};

const visibilityBtnStyle = (active: boolean): React.CSSProperties => ({
  backgroundColor: active ? "#648f8c" : "transparent",
  color: active ? "white" : "#648f8c",
  border: "1px solid #648f8c",
  padding: "8px 16px",
  borderRadius: "8px",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "8px",
  fontSize: "13px",
  fontWeight: "bold",
  transition: "all 0.2s"
});

const columnPickerDropdown: React.CSSProperties = {
  position: "absolute",
  top: "45px",
  right: 0,
  backgroundColor: "#1a1a1a",
  border: "1px solid #333",
  borderRadius: "10px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
  zIndex: 100,
  minWidth: "200px",
  overflow: "hidden"
};

const dropdownItemStyle = (selected: boolean): React.CSSProperties => ({
  padding: "10px 12px",
  display: "flex",
  alignItems: "center",
  gap: "10px",
  cursor: "pointer",
  fontSize: "12px",
  color: selected ? "white" : "#666",
  backgroundColor: selected ? "#648f8c15" : "transparent",
  borderBottom: "1px solid #252525",
  transition: "0.2s"
});

const badgeStyle: React.CSSProperties = {
  backgroundColor: "#648f8c33",
  padding: "6px 15px",
  borderRadius: "20px",
  color: "#648f8c",
  fontSize: "13px",
  border: "1px solid #648f8c33",
  fontWeight: "bold"
};

export default DataConfigPage;