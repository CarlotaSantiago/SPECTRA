import { Settings2, Check } from "lucide-react";
import { DropdownPicker, DropdownItem } from "./ui/DropdownPicker";

/**
 * Propiedades para el selector de columnas.
 */
interface ColumnPickerProps {
  /** Array con todas las columnas disponibles en el dataset */
  allColumns: string[];
  /** Array con los nombres de las columnas que actualmente están visibles */
  visibleColumns: string[];
  /** Estado de apertura del panel desplegable */
  isOpen: boolean;
  /** Callback para alternar el estado de apertura */
  onToggleOpen: () => void;
  /** Callback que recibe el nombre de la columna para alternar su visibilidad */
  onToggleColumn: (col: string) => void;
}

/**
 * Componente que permite al usuario filtrar/ocultar columnas en la previsualización
 * del dataset. Extiende `DropdownPicker` para la lógica de apertura y renderizado.
 */
export const ColumnPicker = ({
  allColumns,
  visibleColumns,
  isOpen,
  onToggleOpen,
  onToggleColumn,
}: ColumnPickerProps) => (
  <DropdownPicker
    isOpen={isOpen}
    onToggleOpen={onToggleOpen}
    icon={<Settings2 size={18} />}
    label="Ver/Ocultar Columnas"
    align="right"
    dropdownMinWidth="220px"
    header="MOSTRAR COLUMNAS EN PREVIEW"
  >
    {allColumns.map((col) => {
      const isVisible = visibleColumns.includes(col);
      return (
        <DropdownItem
          key={col}
          isSelected={isVisible}
          onClick={() => onToggleColumn(col)}
        >
          <div style={{ width: 14, display: "flex", alignItems: "center" }}>
            {isVisible && (
              <Check size={14} color="#648f8c" strokeWidth={3} />
            )}
          </div>
          <span
            style={{
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {col}
          </span>
        </DropdownItem>
      );
    })}
  </DropdownPicker>
);