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
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [activeFilterCol, setActiveFilterCol] = useState<string | null>(null);
  const pageSize = 150; // Cantidad de filas por vista
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const activeCols = allColumns.filter((c) => visibleColumns.includes(c));

  // --- LÓGICA DE RESIZE ---
  const handleResize = (colName: string, startX: number, startWidth: number) => {
    const onMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(50, startWidth + (e.clientX - startX));
      setColumnWidths(prev => ({ ...prev, [colName]: newWidth }));
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.cursor = "default";
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    document.body.style.cursor = "col-resize";
  };

  // --- FUNCIÓN PARA PEDIR DATOS AL BACKEND ---
  const fetchPage = async () => {
    setLoading(true);
    try {
      const filterParam = encodeURIComponent(JSON.stringify(filters));
      const response = await fetch(
        `http://localhost:8000/get-page?path=${encodeURIComponent(filePath)}&page=${page}&size=${pageSize}&filters=${filterParam}`
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

  // 1. Sincroniza el número del input cuando la página cambia (por botones o setPage)
  useEffect(() => {
    setInputPage(page.toString());
  }, [page]);

  // 2. Si cambias el ARCHIVO o aplicas un FILTRO nuevo, volvemos a la página 1
  // Esto evita quedarte en la página 50 de un resultado que ahora solo tiene 2 páginas
  useEffect(() => {
    setPage(1);
  }, [filePath, filters]); 

  // 3. LA PETICIÓN PRINCIPAL: Se dispara cuando cambia la página o el archivo.
  // Nota: No incluimos 'filters' aquí porque el efecto anterior ya hace el setPage(1),
  // y ese cambio de 'page' ya disparará este efecto.
  useEffect(() => {
    if (filePath) {
      fetchPage();
    }
  }, [page, filePath]);

  const totalPages = Math.ceil(totalRows / pageSize);

 return (
    <div style={{ display: "flex", flexDirection: "column", flexGrow: 1, overflow: "hidden" }}>
      
      <div style={tableContainerStyle}>
        <table style={{ ...tableStyle, tableLayout: "fixed", width: "fit-content", minWidth: "100%" }}>
          <thead>
            <tr>
              {activeCols.map((col) => {
                const role = roles[col] || "none";
                const width = columnWidths[col] || 150; // Ancho inicial
                const isFiltering = activeFilterCol == col;
                return (
                  <th key={col} style={{ ...getHeaderStyle(role, width), position: 'relative' }}>
                    <div style={headerInnerStyle} onClick={() => onCycleRole(col)}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                         <span style={roleLabelStyle(role)}>{role.toUpperCase()}</span>
                         
                         {/* ICONO DE EMBUDO / FILTRO */}
                         <button 
                            onClick={(e) => {
                                e.stopPropagation();
                                setActiveFilterCol(isFiltering ? null : col);
                            }}
                            style={filterBtnStyle(!!filters[col])}
                         >
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
                         </button>
                      </div>
                      <div style={colNameRowStyle} onClick={() => onCycleRole(col)}>
                        <span style={{ ...colNameStyle, fontSize: "14px" }}>{col}</span>
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
                      {/* INPUT DE FILTRO (Aparece al pulsar el embudo) */}
                      {isFiltering && (
                        <input 
                          autoFocus
                          placeholder="Filtrar..."
                          value={filters[col] || ""}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => setFilters(prev => ({ ...prev, [col]: e.target.value }))}
                          style={filterInputStyle}
                        />
                      )}
                    </div>
                    {/* TIRADOR PARA RESIZE (BARRA INVISIBLE) */}
                    <div
                      onMouseDown={(e) => {
                        e.stopPropagation();
                        handleResize(col, e.clientX, width);
                      }}
                      style={resizerStyle}
                    />
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody style={{ opacity: loading ? 0.4 : 1, transition: "opacity 0.2s" }}>
            {rows.map((row, i) => (
              <tr key={i} style={rowStyle}>
                {activeCols.map((col) => (
                  <td key={col} style={{ ...tdStyle, width: `${columnWidths[col] || 150}px` }}>
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

const resizerStyle: React.CSSProperties = {
  position: "absolute",
  right: 0,
  top: 0,
  bottom: 0,
  width: "5px",
  cursor: "col-resize",
  zIndex: 20,
  transition: "background-color 0.2s",
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

const getHeaderStyle = (role: string, width: number): React.CSSProperties => ({
  position: "sticky",
  top: 0,
  zIndex: 10,
  backgroundColor: "#222",
  padding: "15px 12px",
  textAlign: "left",
  width: `${width}px`,
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

const filterBtnStyle = (active: boolean): React.CSSProperties => ({
  background: "none",
  border: "none",
  color: active ? "#3b82f6" : "#555", // Azul si hay texto filtrado
  cursor: "pointer",
  padding: "2px",
  display: "flex",
  alignItems: "center",
  transition: "color 0.2s"
});

const filterInputStyle: React.CSSProperties = {
  marginTop: "10px",
  width: "100%",
  backgroundColor: "#111",
  border: "1px solid #333",
  borderRadius: "4px",
  padding: "4px 8px",
  color: "#eee",
  fontSize: "11px",
  outline: "none",
  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.5)"
};