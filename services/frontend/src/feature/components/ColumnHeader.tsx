import { ShieldCheck } from "lucide-react";

interface ColumnHeaderProps {
  col: string;
  role: 'feature' | 'target' | 'none';
  isBlindada: boolean;
  onCycleRole: (col: string) => void;
  onToggleBlindar: (e: React.MouseEvent, col: string) => void;
}

export const ColumnHeader = ({ col, role, isBlindada, onCycleRole, onToggleBlindar }: ColumnHeaderProps) => {
  const border = role === 'feature' ? "#3b82f6" : role === 'target' ? "#10b981" : "#444";
  
  return (
    <th 
      style={{ ...headerBaseStyle, borderBottom: `3px solid ${border}` }} 
      onClick={() => onCycleRole(col)}
    >
      <div style={headerContentStyle}>
        <span style={roleBadgeStyle(role)}>{role || 'OFF'}</span>
        <div style={nameRowStyle}>
          <span style={colNameStyle}>{col}</span>
          {role === 'feature' && (
            <ShieldCheck 
              size={14} 
              onClick={(e) => onToggleBlindar(e, col)}
              style={{ color: isBlindada ? "#ef4444" : "#6c6c6c", flexShrink: 0 }} 
            />
          )}
        </div>
      </div>
    </th>
  );
};

// Estilos internos (extraídos para limpiar el TSX)
const headerBaseStyle: React.CSSProperties = {
  padding: "12px 10px", backgroundColor: "#2c2c2c", cursor: "pointer",
  transition: "all 0.2s ease", textAlign: "left", minWidth: "150px",
  position: "sticky", top: 0, zIndex: 10
};
const headerContentStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "4px", overflow: "hidden" };
const roleBadgeStyle = (role: string): React.CSSProperties => ({ fontSize: "8px", color: role !== 'none' ? "inherit" : "#666", textTransform: "uppercase", fontWeight: "bold" });
const nameRowStyle: React.CSSProperties = { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "4px" };
const colNameStyle: React.CSSProperties = { color: "white", fontSize: "11px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" };