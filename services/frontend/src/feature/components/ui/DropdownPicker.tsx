import { useEffect, useRef } from "react";
import { ChevronDown } from "lucide-react";
import { COLORS, RADII } from "../../../styles/tokens";

/**
 * Propiedades del componente base de despliegue.
 */
interface DropdownPickerProps {
  /** Estado de apertura del panel */
  isOpen: boolean;
  /** Handler para abrir/cerrar el panel */
  onToggleOpen: () => void;
  /** Contenido principal del botón trigger */
  label: React.ReactNode;
  /** Icono opcional a la izquierda del label */
  icon?: React.ReactNode;
  /** Alineación del panel desplegado relativa al botón (izquierda o derecha) */
  align?: "left" | "right";
  /** Ancho mínimo CSS para el panel flotante */
  dropdownMinWidth?: string;
  /** Ancho mínimo CSS para el botón trigger */
  buttonMinWidth?: string;
  /** Texto de cabecera opcional para el panel flotante */
  header?: string;
  /** Los nodos hijos (típicamente `DropdownItem`s) a renderizar en la lista */
  children: React.ReactNode;
}

/**
 * Componente UI base (Core) que encapsula la lógica compleja de los menús 
 * desplegables personalizados: control de estado externo, detección de clics 
 * fuera del área (click-outside), animaciones y sistema modular de hijos.
 * Es la base constructiva de `ModelPicker` y `ColumnPicker`.
 */
export const DropdownPicker = ({
  isOpen,
  onToggleOpen,
  label,
  icon,
  align = "right",
  dropdownMinWidth = "220px",
  buttonMinWidth,
  header,
  children,
}: DropdownPickerProps) => {
  const pickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        pickerRef.current &&
        !pickerRef.current.contains(event.target as Node)
      ) {
        onToggleOpen();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onToggleOpen]);

  return (
    <div ref={pickerRef} style={{ position: "relative" }}>
      {/* Botón trigger */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleOpen();
        }}
        style={triggerBtnStyle(isOpen, buttonMinWidth)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {icon}
          {label}
        </div>
        <ChevronDown
          size={14}
          style={{
            transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.3s",
            flexShrink: 0,
          }}
        />
      </button>

      {/* Panel desplegable */}
      {isOpen && (
        <div style={dropdownContainerStyle(align, dropdownMinWidth)}>
          {header && <div style={dropdownHeaderStyle}>{header}</div>}
          <div style={{ maxHeight: "300px", overflowY: "auto" }}>
            {children}
          </div>
        </div>
      )}
    </div>
  );
};


/**
 * Propiedades para un item de la lista desplegable.
 */
interface DropdownItemProps {
  /** Si es true, el item se renderiza con estilos de estado activo/seleccionado */
  isSelected: boolean;
  /** Función a ejecutar cuando el usuario hace clic en el item */
  onClick: () => void;
  /** Contenido del item */
  children: React.ReactNode;
}

export const DropdownItem = ({ isSelected, onClick, children }: DropdownItemProps) => (
  <div onClick={onClick} style={dropdownItemStyle(isSelected)}>
    {children}
  </div>
);


const triggerBtnStyle = (
  active: boolean,
  minWidth?: string
): React.CSSProperties => ({
  backgroundColor: active ? COLORS.primary : "transparent",
  color: active ? "white" : COLORS.primary,
  border: `1px solid ${COLORS.primary}`,
  padding: "8px 16px",
  borderRadius: RADII.md,
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "8px",
  fontSize: "13px",
  fontWeight: "bold",
  transition: "all 0.2s",
  ...(minWidth && { minWidth }),
});

const dropdownContainerStyle = (
  align: "left" | "right",
  minWidth: string
): React.CSSProperties => ({
  position: "absolute",
  top: "45px",
  [align]: 0,
  backgroundColor: COLORS.surface2,
  border: `1px solid ${COLORS.border}`,
  borderRadius: "10px",
  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
  zIndex: 100,
  minWidth,
  overflow: "hidden",
});

const dropdownHeaderStyle: React.CSSProperties = {
  padding: "10px 12px",
  fontSize: "10px",
  color: COLORS.textDim,
  fontWeight: "bold",
  borderBottom: `1px solid ${COLORS.border}`,
  letterSpacing: "0.5px",
  textTransform: "uppercase",
};

const dropdownItemStyle = (selected: boolean): React.CSSProperties => ({
  padding: "10px 12px",
  display: "flex",
  alignItems: "center",
  gap: "10px",
  cursor: "pointer",
  fontSize: "12px",
  color: selected ? "white" : "#888",
  backgroundColor: selected ? `${COLORS.primary}22` : "transparent",
  borderBottom: `1px solid ${COLORS.borderLight}`,
  transition: "background-color 0.2s",
});
