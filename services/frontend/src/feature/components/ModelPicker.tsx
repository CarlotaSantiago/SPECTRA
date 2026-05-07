import { Bot, Check, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

interface ModelPickerProps {
  allModels: string[];
  selectedModel: string;
  isOpen: boolean;
  onToggleOpen: () => void;
  onSelectModel: (model: string) => void;
}

// --- ESTILOS COMPARTIDOS CON TU COLUMN PICKER ---
const pickerBtnStyle = (active: boolean): React.CSSProperties => ({
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
  transition: "all 0.2s",
  minWidth: "220px",
  justifyContent: "space-between"
});

const dropdownContainerStyle: React.CSSProperties = {
  position: "absolute",
  top: "45px",
  left: 0, // El tuyo usa right: 0, este lo pongo a la izquierda para que no choque
  backgroundColor: "#1a1a1a",
  border: "1px solid #333",
  borderRadius: "10px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
  zIndex: 100,
  minWidth: "250px",
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

const dropdownItemStyle = (isSelected: boolean): React.CSSProperties => ({
  padding: "10px 12px",
  display: "flex",
  alignItems: "center",
  gap: "10px",
  cursor: "pointer",
  fontSize: "12px",
  color: isSelected ? "white" : "#888",
  backgroundColor: isSelected ? "#648f8c22" : "transparent",
  borderBottom: "1px solid #252525",
  transition: "0.2s"
});

export const ModelPicker = ({ 
  allModels, 
  selectedModel, 
  isOpen, 
  onToggleOpen, 
  onSelectModel 
}: ModelPickerProps) => {
  const pickerRef = useRef<HTMLDivElement>(null);

  // FILTRO DEL PROFE: Quitamos modelos que contienen "coder"
  const filteredModels = allModels;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isOpen && pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
        onToggleOpen();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onToggleOpen]);

  return (
    <div ref={pickerRef} style={{ position: "relative" }}>
      {/* Botón Principal */}
      <button 
        onClick={(e) => {
          e.stopPropagation();
          onToggleOpen();
        }} 
        style={pickerBtnStyle(isOpen)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Bot size={18} /> 
          {selectedModel || "Seleccionar Modelo"}
        </div>
        <ChevronDown size={14} style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: '0.3s' }}/>
      </button>
      
      {/* Listado de Modelos */}
      {isOpen && (
        <div style={dropdownContainerStyle}>
          <div style={dropdownHeaderStyle}>MODELOS LLM RECOMENDADOS</div>
          
          <div style={{ maxHeight: "300px", overflowY: "auto" }}>
            {filteredModels.length === 0 && (
              <div style={{ padding: "12px", fontSize: "12px", color: "#555" }}>No hay modelos disponibles</div>
            )}
            {filteredModels.map((m) => {
              const isSelected = selectedModel === m;
              return (
                <div 
                  key={m} 
                  onClick={() => {
                    onSelectModel(m);
                    onToggleOpen(); // Se cierra al elegir uno
                  }} 
                  style={dropdownItemStyle(isSelected)}
                >
                  <div style={{ width: 14, display: "flex", alignItems: "center" }}>
                    {isSelected && <Check size={14} color="#648f8c" strokeWidth={3} />}
                  </div>
                  
                  <span style={{ whiteSpace: "nowrap" }}>{m}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};