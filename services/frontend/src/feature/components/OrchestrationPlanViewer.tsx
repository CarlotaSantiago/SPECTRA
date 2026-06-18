import { ChevronUp, ChevronDown } from "lucide-react";

/**
 * Propiedades esperadas por el visor de orquestación.
 */
interface PlanViewerProps {
  /** Objeto que define la estrategia, orden y condicionales (GatedChain, etc.) */
  plan: any;
  /** Callback disparado cuando el usuario reordena un elemento en la UI */
  onMoveItem: (idx: number, dir: "up" | "down") => void;
}

/**
 * Componente recursivo que renderiza visualmente el plan lógico de orquestación
 * devuelto por el backend. Permite al usuario reordenar la cadena de predicción
 * y visualizar estructuras complejas como árboles condicionales (GatedChain).
 * 
 * @param props - `plan` (el objeto de estrategia) y `onMoveItem` (manejador de reordenamiento).
 */
export const OrchestrationPlanViewer = ({ plan, onMoveItem }: PlanViewerProps) => {
  if (!plan) return null;

  const { strategy, order, gating, dependents, sub_strategy } = plan;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={strategyLabelStyle}>{strategy}</div>

      {order && order.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {order.map((target: string, i: number) => (
            <div key={target} style={orderItemStyle}>
              <span>
                {i + 1}. {target}
              </span>
              <div style={{ display: "flex", gap: "4px" }}>
                <button
                  onClick={() => onMoveItem(i, "up")}
                  disabled={i === 0}
                  style={miniBtnStyle}
                  aria-label={`Mover ${target} arriba`}
                >
                  <ChevronUp size={14} />
                </button>
                <button
                  onClick={() => onMoveItem(i, "down")}
                  disabled={i === order.length - 1}
                  style={miniBtnStyle}
                  aria-label={`Mover ${target} abajo`}
                >
                  <ChevronDown size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {strategy === "GatedChain" && (
        <div style={gatingContainerStyle}>
          <div style={{ ...orderItemStyle, borderLeft: "3px solid #ff6b6b", backgroundColor: "#1a1212" }}>
            <span style={{ color: "#ff6b6b" }}>
              Variable Condicional: <strong>{gating}</strong>
            </span>
          </div>

          <div style={{ fontSize: "11px", color: "#aaa", margin: "6px 0 4px 4px" }}>
            Dependientes directos (Si {gating} está presente):
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginBottom: "10px", paddingLeft: "4px" }}>
            {dependents?.map((dep: string) => (
              <span key={dep} style={chipStyle}>
                {dep}
              </span>
            ))}
          </div>

          {sub_strategy && (
            <div style={subStrategyStyle}>
              <OrchestrationPlanViewer plan={sub_strategy} onMoveItem={onMoveItem} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const strategyLabelStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#648f8c",
  fontWeight: "bold",
  textTransform: "uppercase",
  marginBottom: "2px",
};

const orderItemStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "8px 12px",
  backgroundColor: "#121212",
  borderRadius: "6px",
  fontSize: "13px",
  color: "#ccc",
  borderLeft: "3px solid #648f8c",
  marginBottom: "4px",
};

const miniBtnStyle: React.CSSProperties = {
  background: "#1e1e1e",
  border: "1px solid #333",
  color: "#648f8c",
  borderRadius: "4px",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "2px",
};

const chipStyle: React.CSSProperties = {
  fontSize: "11px",
  backgroundColor: "#222",
  color: "#ccc",
  padding: "3px 8px",
  borderRadius: "4px",
  border: "1px solid #333",
};

const gatingContainerStyle: React.CSSProperties = {
  borderLeft: "2px dashed #ff6b6b",
  paddingLeft: "10px",
  marginTop: "4px",
};

const subStrategyStyle: React.CSSProperties = {
  marginTop: "10px",
  backgroundColor: "rgba(255,255,255,0.02)",
  padding: "8px",
  borderRadius: "6px",
};
