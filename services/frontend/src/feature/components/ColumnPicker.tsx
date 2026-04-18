import { Settings2, Check } from "lucide-react";
import { useEffect, useRef } from "react"; // 1. Importar hooks

interface ColumnPickerProps {
  allColumns: string[];
  visibleColumns: string[];
  isOpen: boolean;
  onToggleOpen: () => void;
  onToggleColumn: (col: string) => void;
}

// --- ESTILOS DINÁMICOS ---
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

const dropdownItemStyle = (selected: boolean): React.CSSProperties => ({
  padding: "10px 12px",
  display: "flex",
  alignItems: "center",
  gap: "10px",
  cursor: "pointer",
  fontSize: "12px",
  color: selected ? "white" : "#888",
  backgroundColor: selected ? "#648f8c22" : "transparent",
  borderBottom: "1px solid #252525",
  transition: "0.2s"
});

// --- ESTILOS ESTÁTICOS ---
const dropdownContainerStyle: React.CSSProperties = {
  position: "absolute",
  top: "45px",
  right: 0,
  backgroundColor: "#1a1a1a",
  border: "1px solid #333",
  borderRadius: "10px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
  zIndex: 100, // Vital para que flote sobre la tabla
  minWidth: "220px",
  overflow: "hidden"
};

const dropdownHeaderStyle: React.CSSProperties = {
  padding: "10px 12px",
  fontSize: "10px",
  color: "#555",
  fontWeight: "bold",
  borderBottom: "1px solid #333",
  letterSpacing: "0.5px"
};

export const ColumnPicker = ({ 
  allColumns, 
  visibleColumns, 
  isOpen, 
  onToggleOpen, 
  onToggleColumn 
}: ColumnPickerProps) => {
    const pickerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Si el menú está abierto y el clic NO está dentro del pickerRef
      if (isOpen && pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        onToggleOpen(); // Esto cerrará el menú
      }
    };

    // Añadir el escuchador de eventos al documento
    document.addEventListener("mousedown", handleClickOutside);
    
    // Limpiar el evento al desmontar el componente para evitar fugas de memoria
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
    }, [isOpen, onToggleOpen]);

  return (
    <div ref={pickerRef} style={{ position: "relative" }}>
      {/* Botón que dispara el dropdown */}
      <button 
        onClick={(e) => {
          e.stopPropagation(); // Evita que clicks cierren y abran accidentalmente
          onToggleOpen();
        }} 
        style={visibilityBtnStyle(isOpen)}
      >
        <Settings2 size={18} /> Ver/Ocultar Columnas
      </button>
      
      {/* Contenedor del Dropdown */}
      {isOpen && (
        <div style={dropdownContainerStyle}>
          <div style={dropdownHeaderStyle}>MOSTRAR COLUMNAS EN PREVIEW</div>
          
          <div style={{ maxHeight: "300px", overflowY: "auto" }}>
            {allColumns.map((col) => {
              const isVisible = visibleColumns.includes(col);
              return (
                <div 
                  key={col} 
                  onClick={() => onToggleColumn(col)} 
                  style={dropdownItemStyle(isVisible)}
                >
                  {/* Icono de Check o espacio vacío para alineación */}
                  <div style={{ width: 14, display: "flex", alignItems: "center" }}>
                    {isVisible && <Check size={14} color="#648f8c" strokeWidth={3} />}
                  </div>
                  
                  <span style={{ 
                    whiteSpace: "nowrap", 
                    overflow: "hidden", 
                    textOverflow: "ellipsis" 
                  }}>
                    {col}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};