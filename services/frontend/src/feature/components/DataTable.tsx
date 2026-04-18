import { ShieldCheck } from "lucide-react";

interface DataTableProps {
  previewData: any[];
  allColumns: string[];
  visibleColumns: string[];
  roles: Record<string, 'feature' | 'target' | 'none'>;
  blindadas: Record<string, boolean>;
  onCycleRole: (col: string) => void;
  onToggleBlindar: (e: React.MouseEvent, col: string) => void;
}

export const DataTable = ({
  previewData,
  allColumns,
  visibleColumns,
  roles,
  blindadas,
  onCycleRole,
  onToggleBlindar
}: DataTableProps) => {
  const activeCols = allColumns.filter((c) => visibleColumns.includes(c));

  return (
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
        <tbody>
          {previewData.map((row, i) => (
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
  );
};

// --- ESTILOS CORREGIDOS (Adiós a los espacios feos) ---

const tableContainerStyle: React.CSSProperties = {
  flexGrow: 1,
  overflow: "auto",
  borderRadius: "8px",
  border: "1px solid #252525",
  backgroundColor: "#1a1a1a", // Fondo base de la tabla
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse", // CRUCIAL: Elimina el espacio entre celdas
  tableLayout: "fixed",
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