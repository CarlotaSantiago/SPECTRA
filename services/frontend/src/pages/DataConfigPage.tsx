import { useLocation, useNavigate } from "react-router-dom";
import { useState, useMemo } from "react";
import { ShieldCheck, Target, Database, ArrowRight, Table, Info, Eye, EyeOff, ListFilter, Settings2 } from "lucide-react";

const DataConfigPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const data = location.state?.data;

  // 1. Configuración de columnas visibles
  const columnasIniciales = ["idbuzon", "descrip", "edad", "servpeti", "numpeti", "desprest", "datosclini", "sospechadiag"];
  
  const [visibleColumns, setVisibleColumns] = useState<string[]>(columnasIniciales);
  const [showColumnPicker, setShowColumnPicker] = useState(false);
  
  // 2. Estados de Roles y Blindaje
  const [roles, setRoles] = useState<Record<string, 'feature' | 'target' | 'none'>>({});
  const [blindadas, setBlindadas] = useState<Record<string, boolean>>({});

  if (!data) return <div style={{ padding: "50px", textAlign: "center" }}>No hay datos.</div>;

  const toggleColumnVisibility = (col: string) => {
    setVisibleColumns(prev => 
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    );
  };

  const handleRoleChange = (col: string, role: 'feature' | 'target' | 'none') => {
    setRoles(prev => ({ ...prev, [col]: role }));
  };

  const handleNextStep = () => {
    const dossier = {
      n_total: data.n_total,
      path: data.path_final,
      features: Object.keys(roles).filter(k => roles[k] === 'feature'),
      targets: Object.keys(roles).filter(k => roles[k] === 'target'),
      mandatory: Object.keys(blindadas).filter(k => blindadas[k] && roles[k] === 'feature')
    };
    navigate("/prediction", { state: { dossier } });
  };

  return (
    <div style={{ padding: "30px", margin: "0 auto", backgroundColor: "#31313133", minHeight: "100vh" }}>
      
      <button onClick={() => navigate(-1)} style={{ position: "absolute", top: "20px", left: "20px", backgroundColor: "transparent", border: "none", color: "#648f8c", display: "flex", alignItems: "center", gap: "5px", cursor: "pointer" }}>
      <ArrowRight size={16} style={{ transform: "rotate(180deg)" }} /> Volver
    </button>
    
      {/* HEADER */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ color: "#4a6b68", margin: 0, display: "flex", alignItems: "center", gap: "10px" }}>
            <Database size={28} /> Etapa 0: Configuración y Selección
          </h2>
          <div style={{ display: "flex", gap: "10px" }}>
            <button 
              onClick={() => setShowColumnPicker(!showColumnPicker)} 
              style={visibilityBtnStyle(showColumnPicker)}
            >
              <Settings2 size={18} /> Ver/Ocultar Columnas
            </button>
            <div style={badgeStyle}>N = {data.n_total}</div>
          </div>
        </div>

        {/* SELECTOR DE COLUMNAS (DROPDOWN) */}
        {showColumnPicker && (
          <div style={columnPickerDropdown}>
            <p style={{ fontSize: "12px", fontWeight: "bold", marginBottom: "10px" }}>Selecciona columnas para la tabla:</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "5px" }}>
              {data.columnas.map((col: string) => (
                <label key={col} style={{ fontSize: "12px", display: "flex", alignItems: "center", gap: "5px", cursor: "pointer" }}>
                  <input 
                    type="checkbox" 
                    checked={visibleColumns.includes(col)} 
                    onChange={() => toggleColumnVisibility(col)} 
                  />
                  {col}
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "20px", marginTop: "20px" }}>
        
        {/* TABLA DE PREVISUALIZACIÓN FILTRADA */}
        <div style={cardStyle}>
          <h3 style={{ fontSize: "16px", marginBottom: "15px", color: "#536765", display: "flex", alignItems: "center", gap: "8px" }}>
            <Table size={20} /> Vista Previa ({visibleColumns.length} columnas visibles)
          </h3>
          <div style={{ overflowX: "auto", borderRadius: "10px", border: "1px solid #648f8c" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead style={{ backgroundColor: "#31313133" }}>
                <tr>
                  {data.columnas.filter((c: string) => visibleColumns.includes(c)).map((col: string) => (
                    <th key={col} style={previewThStyle}>
                      <span style={{ color: roles[col] === 'target' ? '#50a388' : roles[col] === 'feature' ? '#5d83bf' : '#b4b4b4' }}>
                        {col}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.preview.map((row: any, i: number) => (
                  <tr key={i} style={{ borderBottom: "1px solid #648f8c" }}>
                    {data.columnas.filter((c: string) => visibleColumns.includes(c)).map((col: string) => (
                      <td key={col} style={previewTdStyle}>{row[col]?.toString().substring(0, 40)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* PANEL DE ROLES (Muestra todas para poder configurar incluso las ocultas) */}
        <div style={{ ...cardStyle, maxHeight: "75vh", overflowY: "auto" }}>
          <h3 style={{ fontSize: "16px", color: "#536765", marginBottom: "15px" }}>Configurar Roles</h3>
          {data.columnas.map((col: string) => (
            <div key={col} style={colSelectorCard(roles[col])}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: "bold", fontSize: "13px" }}>{col}</span>
                <div style={{ display: "flex", gap: "5px" }}>
                  {roles[col] === 'feature' && (
                    <ShieldCheck 
                      size={16} 
                      onClick={() => setBlindadas(p => ({...p, [col]: !p[col]}))}
                      style={{ cursor: "pointer", color: blindadas[col] ? "#ef4444" : "#ccc" }} 
                    />
                  )}
                  {visibleColumns.includes(col) ? <Eye size={16} color="#648f8c"/> : <EyeOff size={16} color="#ccc"/>}
                </div>
              </div>
              <div style={{ display: "flex", gap: "3px", marginTop: "8px" }}>
                <button onClick={() => handleRoleChange(col, 'feature')} style={miniBtn(roles[col] === 'feature', "#3b82f6")}>FEATURE</button>
                <button onClick={() => handleRoleChange(col, 'target')} style={miniBtn(roles[col] === 'target', "#10b981")}>TARGET</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button onClick={handleNextStep} style={mainBtnStyle}>
        Confirmar Selección y Avanzar <ArrowRight size={22} />
      </button>
    </div>
  );
};

// --- ESTILOS ---
const visibilityBtnStyle = (active: boolean) => ({
  display: "flex",
  alignItems: "center",
  gap: "8px",
  padding: "8px 16px",
  borderRadius: "8px",
  border: "1px solid #648f8c",
  backgroundColor: active ? "#648f8c" : "transparent",
  color: active ? "white" : "#648f8c",
  cursor: "pointer",
  fontSize: "13px",
  fontWeight: "bold" as any
});

const columnPickerDropdown: React.CSSProperties = {
  marginTop: "15px",
  padding: "15px",
  backgroundColor: "#31313133",
  border: "1px solid #31313133",
  borderRadius: "10px",
  boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)"
};

const cardStyle: React.CSSProperties = {
  background: "#78787833", padding: "20px", borderRadius: "15px",
  boxShadow: "0 4px 20px rgba(0,0,0,0.05)", border: "1px solid #31313133"
};

const badgeStyle: React.CSSProperties = {
  backgroundColor: "#648f8c", padding: "8px 15px", borderRadius: "20px",
  color: "white", fontSize: "14px", border: "1px solid #648f8c33", fontWeight: "bold"
};

const colSelectorCard = (role: string) => ({
  backgroundColor: role === 'target' ? "#31313133" : role === 'feature' ? "#31313133" : "#31313133",
  padding: "10px", borderRadius: "8px", marginBottom: "8px",
  border: `1px solid ${role === 'target' ? "#a4ffc4" : role === 'feature' ? "#92c1fb" : "#c3c3c3"}`
});

const miniBtn = (active: boolean, color: string) => ({
  flex: 1, padding: "4px", fontSize: "10px", borderRadius: "4px", border: "none",
  backgroundColor: active ? color : "#648f8c", color: active ? "white" : "#d2d2d2",
  cursor: "pointer", fontWeight: "bold" as any
});

const mainBtnStyle: React.CSSProperties = {
  marginTop: "20px", width: "100%", padding: "18px", borderRadius: "15px", border: "none",
  backgroundColor: "#648f8c", color: "white", fontSize: "18px", fontWeight: "bold",
  cursor: "pointer", display: "flex", justifyContent: "center", alignItems: "center", gap: "12px"
};

const previewThStyle: React.CSSProperties = {
  padding: "8px",
  borderRight: "1px solid #648f8c",
  textAlign: "left",
  fontSize: "11px",
  backgroundColor: "#648f8c33",
  // Quitamos whiteSpace: "nowrap" para que el título pueda romper línea si es necesario
  width: "auto", 
  minWidth: "100px"
};

const previewTdStyle: React.CSSProperties = {
  padding: "6px 8px",
  borderRight: "1px solid #648f8c",
  color: "#d4d4d4",
  // CAMBIO CLAVE:
  wordBreak: "break-word", // Rompe palabras largas
  whiteSpace: "normal",    // Permite saltos de línea
  fontSize: "11px",
  lineHeight: "1.2",
  maxWidth: "200px"        // Limita el ancho máximo de cada celda
};

export default DataConfigPage;