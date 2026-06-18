import { Bot, Check } from "lucide-react";
import { DropdownPicker, DropdownItem } from "./ui/DropdownPicker";

/**
 * Propiedades para el selector de modelos.
 */
interface ModelPickerProps {
  /** Array con los nombres formateados de los modelos disponibles */
  allModels: string[];
  /** Modelo actualmente seleccionado */
  selectedModel: string;
  /** Determina si el menú desplegable está visible */
  isOpen: boolean;
  /** Callback para alternar la visibilidad del menú */
  onToggleOpen: () => void;
  /** Callback ejecutado al seleccionar un modelo de la lista */
  onSelectModel: (model: string) => void;
}


/**
 * Componente encapsulado para la selección de modelos LLM.
 * Reutiliza la base interactiva `DropdownPicker` para evitar lógica duplicada de UI.
 */
export const ModelPicker = ({
  allModels,
  selectedModel,
  isOpen,
  onToggleOpen,
  onSelectModel,
}: ModelPickerProps) => (
  <DropdownPicker
    isOpen={isOpen}
    onToggleOpen={onToggleOpen}
    icon={<Bot size={18} />}
    label={selectedModel || "Seleccionar Modelo"}
    align="left"
    dropdownMinWidth="250px"
    buttonMinWidth="220px"
    header="MODELOS LLM DISPONIBLES"
  >
    {allModels.length === 0 && (
      <div style={{ padding: "12px", fontSize: "12px", color: "#555" }}>
        No hay modelos disponibles
      </div>
    )}
    {allModels.map((m) => (
      <DropdownItem
        key={m}
        isSelected={selectedModel === m}
        onClick={() => {
          onSelectModel(m);
          onToggleOpen();
        }}
      >
        <div style={{ width: 14, display: "flex", alignItems: "center" }}>
          {selectedModel === m && (
            <Check size={14} color="#648f8c" strokeWidth={3} />
          )}
        </div>
        <span style={{ whiteSpace: "nowrap" }}>{m}</span>
      </DropdownItem>
    ))}
  </DropdownPicker>
);