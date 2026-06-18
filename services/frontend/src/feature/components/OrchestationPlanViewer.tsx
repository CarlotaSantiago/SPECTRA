import { ChevronUp, ChevronDown } from "lucide-react";

interface PlanViewerProps {
  plan: any;
  onMoveItem: (idx: number, dir: 'up' | 'down') => void;
}

export const OrchestrationPlanViewer = ({ plan, onMoveItem }: PlanViewerProps) => {
  if (!plan) return null;

  const { strategy, order, gating, dependents, sub_strategy } = plan;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ fontSize: '11px', color: '#648f8c', fontWeight: 'bold', textTransform: 'uppercase', marginBottom: '2px' }}>
        Estrategia: {strategy}
      </div>

      {order && order.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {order.map((target: string, i: number) => (
            <div key={target} style={orderItemEditable}>
              <span>{i + 1}. {target}</span>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button onClick={() => onMoveItem(i, 'up')} disabled={i === 0} style={miniBtnStyle}>
                  <ChevronUp size={14}/>
                </button>
                <button onClick={() => onMoveItem(i, 'down')} disabled={i === order.length - 1} style={miniBtnStyle}>
                  <ChevronDown size={14}/>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {strategy === "GatedChain" && (
        <div style={{ borderLeft: '2px dashed #ff6b6b', paddingLeft: '10px', marginTop: '4px' }}>
          <div style={{ ...orderItemEditable, borderLeft: '3px solid #ff6b6b', backgroundColor: '#1a1212' }}>
            <span style={{ color: '#ff6b6b' }}>Variable Condicional: <strong>{gating}</strong></span>
          </div>

          <div style={{ fontSize: '11px', color: '#aaa', margin: '6px 0 4px 4px' }}>
            Dependientes directos (Si {gating} está presente):
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '10px', paddingLeft: '4px' }}>
            {dependents?.map((dep: string) => (
              <span key={dep} style={chipStyle}>
                {dep}
              </span>
            ))}
          </div>

          {sub_strategy && (
            <div style={{ marginTop: '10px', backgroundColor: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '6px' }}>
              <OrchestrationPlanViewer plan={sub_strategy} onMoveItem={onMoveItem} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const orderItemEditable: React.CSSProperties = {
  display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", backgroundColor: "#121212", borderRadius: "6px", fontSize: "13px", color: "#ccc", borderLeft: "3px solid #648f8c", marginBottom: "4px"
};
const miniBtnStyle: React.CSSProperties = {
  background: "#1e1e1e", border: "1px solid #333", color: "#648f8c", borderRadius: "4px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", padding: "2px"
};
const chipStyle: React.CSSProperties = {
  fontSize: '11px', backgroundColor: '#222', color: '#ccc', padding: '3px 8px', borderRadius: '4px', border: '1px solid #333'
};