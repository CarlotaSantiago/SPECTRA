import { ShieldCheck, ChevronLeft, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";


interface DataTableProps {
  filePath: string; // Recibimos el path del archivo guardado en el server
  allColumns: string[];
  visibleColumns: string[];
  roles: Record<string, 'feature' | 'target' | 'none'>;
  blindadas: Record<string, boolean>;
  onCycleRole: (col: string) => void;
  onToggleBlindar: (e: React.MouseEvent, col: string) => void;
}

export const DataTable = ({
  filePath,
  allColumns,
  visibleColumns,
  roles,
  blindadas,
  onCycleRole,
  onToggleBlindar
}: DataTableProps) => {
  const [rows, setRows] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [totalRows, setTotalRows] = useState(0);
  const [inputPage, setInputPage] = useState(page.toString());
  const [loading, setLoading] = useState(false);
  const pageSize = 150; // Cantidad de filas por vista
  const activeCols = allColumns.filter((c) => visibleColumns.includes(c));

  // --- FUNCIÓN PARA PEDIR DATOS AL BACKEND ---
  const fetchPage = async () => {
    setLoading(true);
    try {
      // Llamamos al endpoint que creamos antes en FastAPI
      const response = await fetch(
        `http://localhost:8000/get-page?path=${encodeURIComponent(filePath)}&page=${page}&size=${pageSize}`
      );
      const result = await response.json();
      
      if (result.status === "ok") {
        setRows(result.items);
        setTotalRows(result.n_rows);
      }
    } catch (error) {
      console.error("Error cargando página de servidor:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setInputPage(page.toString());
  }, [page]);

  // DISPARAR LA PETICIÓN AL SERVIDOR
  useEffect(() => {
    if (filePath) {
      fetchPage();
    }
  }, [page, filePath]); // Importante: escucha ambos

  useEffect(() => {
    setPage(1);
  }, [filePath]);

  const totalPages = Math.ceil(totalRows / pageSize);

 return (
    <div style={{ display: "flex", flexDirection: "column", flexGrow: 1, overflow: "hidden" }}>
      
      <div style={tableContainerStyle}>
        <table style={tableStyle}>
          <thead>
            <tr>
              {activeCols.map((col) => {
                const role = roles[col] || "none";
                return (
                  <th key={col} style={getHeaderStyle(role)} onClick={() => onCycleRole(col)}>
                    <div style={headerInnerStyle}>
                      <span style={roleLabelStyle(role)}>{role.toUpperCase()}</span>
                      <div style={colNameRowStyle}>
                        <span style={colNameStyle}>{col}</span>
                        {role === "feature" && (
                          <ShieldCheck
                            size={14}
                            onClick={(e) => onToggleBlindar(e, col)}
                            style={{
                              color: blindadas[col] ? "#ef4444" : "#6c6c6c",
                              transition: "color 0.2s"
                            }}
                          />
                        )}
                      </div>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody style={{ opacity: loading ? 0.4 : 1, transition: "opacity 0.2s" }}>
            {rows.map((row, i) => (
              <tr key={i} style={rowStyle}>
                {activeCols.map((col) => (
                  <td key={col} style={tdStyle}>
                    {row[col]?.toString() || "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* --- CONTROLES DE PAGINACIÓN --- */}
      <div style={paginationBarStyle}>
  <div style={{ color: "#666", fontSize: "13px" }}>
    Mostrando {rows.length} de <strong>{totalRows.toLocaleString()}</strong> registros
  </div>
  
  <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
    {/* Botón Anterior */}
    <button 
      disabled={page === 1 || loading} 
      onClick={() => setPage(p => p - 1)}
      style={pageBtnStyle(page === 1 || loading)}
    >
      <ChevronLeft size={18} />
    </button>
    
    {/* INPUT PARA ESCRIBIR LA PÁGINA */}
    <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", color: "#ccc" }}>
      <span>Página</span>
      <input 
        type="text"
        value={inputPage}
        onChange={(e) => setInputPage(e.target.value.replace(/\D/g, ''))} // Solo números
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            const p = parseInt(inputPage);
            if (p > 0 && p <= totalPages) {
              setPage(p);
            } else {
              setInputPage(page.toString()); // Reset si pone una locura
            }
          }
        }}
        style={inputPageStyle}
      />
      <span style={{ color: "#555" }}>de</span>
      <span style={{ fontWeight: "bold", color: "white" }}>{totalPages}</span>
    </div>

      {/* Botón Siguiente */}
      <button 
        disabled={page >= totalPages || loading} 
        onClick={() => setPage(p => p + 1)}
        style={pageBtnStyle(page >= totalPages || loading)}
      >
        <ChevronRight size={18} />
      </button>
    </div>
  </div>
    </div>
  );
};

// --- ESTILOS CORREGIDOS (Adiós a los espacios feos) ---
const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse", // CRUCIAL: Elimina el espacio entre celdas
  tableLayout: "fixed",
};

const inputPageStyle: React.CSSProperties = {
  width: "40px",
  backgroundColor: "#222",
  border: "1px solid #444",
  borderRadius: "4px",
  color: "#648f8c",
  textAlign: "center",
  padding: "2px 4px",
  fontSize: "13px",
  fontWeight: "bold",
  outline: "none",
  transition: "border-color 0.2s"
};

const getHeaderStyle = (role: string): React.CSSProperties => ({
  position: "sticky",
  top: 0,
  zIndex: 10,
  backgroundColor: "#222",
  padding: "12px 10px",
  textAlign: "left",
  cursor: "pointer",
  borderBottom: `2px solid ${
    role === "feature" ? "#3b82f6" : role === "target" ? "#10b981" : "#333"
  }`,
  transition: "background-color 0.2s",
  // Eliminamos cualquier borde lateral que cree espacios
  borderLeft: "none",
  borderRight: "none",
});

const headerInnerStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "4px",
};

const roleLabelStyle = (role: string): React.CSSProperties => ({
  fontSize: "9px",
  fontWeight: "bold",
  color: role === "none" ? "#555" : "inherit",
  letterSpacing: "0.5px",
});

const colNameRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "8px",
};

const colNameStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "white",
  fontWeight: "600",
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

const rowStyle: React.CSSProperties = {
  borderBottom: "1px solid #252525",
};

const tdStyle: React.CSSProperties = {
  padding: "12px 10px",
  fontSize: "11px",
  color: "#aaa",
  whiteSpace: "normal",
  wordBreak: "break-all",
  verticalAlign: "top",
  lineHeight: "1.4",
  // Opcional: un borde sutil a la derecha para separar columnas sin dejar huecos
  borderRight: "1px solid #222",
};

const paginationBarStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "15px 10px",
  backgroundColor: "#121212",
  borderTop: "1px solid #252525"
};

const pageBtnStyle = (disabled: boolean): React.CSSProperties => ({
  backgroundColor: "transparent",
  border: "1px solid #333",
  color: disabled ? "#333" : "#648f8c",
  borderRadius: "6px",
  padding: "5px 10px",
  cursor: disabled ? "not-allowed" : "pointer",
  display: "flex",
  alignItems: "center",
  transition: "all 0.2s"
});

// Mantén tus estilos anteriores (tableContainerStyle, getHeaderStyle, etc.)
// SOLO asegúrate de que tableContainerStyle tenga:
const tableContainerStyle: React.CSSProperties = {
  flexGrow: 1,
  overflow: "auto",
  borderRadius: "8px 8px 0 0", // Redondeado solo arriba
  border: "1px solid #252525",
  backgroundColor: "#1a1a1a",
};