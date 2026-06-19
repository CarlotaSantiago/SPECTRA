import React from "react";

interface EvaluationCardProps {
  name: string;
  feat: any;
  isTarget: boolean;
  technicalMap: Record<number, string>;
  metricOptions: string[];
  onEditField: (name: string, field: string, value: string) => void;
  onUpdateMapping: (name: string, key: string, val: number) => void;
  onUpdateMetrics?: (name: string, metric: string) => void;
}

export const EvaluationCard = ({
  name,
  feat,
  isTarget,
  technicalMap,
  metricOptions,
  onEditField,
  onUpdateMapping,
  onUpdateMetrics
}: EvaluationCardProps) => {

  const parseMapping = (mappingStr: any) => {
    if (!mappingStr || typeof mappingStr !== "string") return [];
    try {
      const cleanStr = mappingStr.replace(/[{}]/g, "");
      if (!cleanStr) return [];
      return cleanStr.split(",").map(pair => {
        const [key, val] = pair.split(":").map(s => s.trim());
        return { key, val: parseInt(val) };
      }).sort((a, b) => a.val - b.val);
    } catch (e) {
      return [];
    }
  };

  return (
    <div style={featureCard}>
      <div style={featureHeader}>
        <span style={featureName}>{name}</span>
        <select 
          value={feat.subclass} 
          onChange={(e) => onEditField(name, 'subclass', e.target.value)} 
          style={selectStyle}
        >
          <option value="NOMINAL">NOMINAL</option>
          <option value="ORDINAL">ORDINAL</option>
          {!isTarget && <option value="BINARY">BINARY</option>}
          {!isTarget && <option value="TEXT_NLP">TEXT_NLP</option>}
        </select>
      </div>

      <label style={labelStyle}>Razonamiento Semántico:</label>
      <textarea 
        style={textAreaStyle} 
        value={feat.reasoning || ""} 
        onChange={(e) => onEditField(name, 'reasoning', e.target.value)} 
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
        <span>Tipo Técnico:</span> 
        <strong style={{ color: '#648f8c' }}>{technicalMap[feat.technical_level] || "Desconocido"}</strong>
      </div>

      <div style={{ marginTop: '10px', borderTop: '1px solid #333', paddingTop: '10px' }}>
        <label style={labelStyle}>Mapeo Ordinal / Jerarquía:</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginTop: '8px' }}>
          {parseMapping(feat.mapping).map((item) => (
            <div key={item.key} style={mappingRowStyle}>
              <span style={{ color: '#ccc' }}>{item.key}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px', color: '#648f8c' }}>Valor:</span>
                <input
                  type="number"
                  value={item.val}
                  onChange={(e) => onUpdateMapping(name, item.key, Number.isNaN(parseInt(e.target.value)) ? 0 : parseInt(e.target.value))}
                  style={mappingInputStyle}
                />
              </div>
            </div>
          ))}
          {parseMapping(feat.mapping).length === 0 && (
            <span style={{ fontSize: '11px', color: '#666', fontStyle: 'italic' }}>Sin mapeo definido (Nominal)</span>
          )}
        </div>
      </div>

      {isTarget && onUpdateMetrics && (
        <div style={{ marginTop: '10px', borderTop: '1px solid #333', paddingTop: '10px' }}>
          <label style={labelStyle}>Métricas de Prioridad:</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '8px' }}>
            {metricOptions.map((metric) => {
              const isSelected = feat.priority_metrics?.includes(metric);
              return (
                <button
                  key={metric}
                  onClick={() => onUpdateMetrics(name, metric)}
                  style={{
                    background: isSelected ? '#648f8c' : '#121212',
                    color: isSelected ? 'white' : '#648f8c',
                    border: `1px solid ${isSelected ? '#648f8c' : '#333'}`,
                    padding: '4px 8px', fontSize: '10px', borderRadius: '4px', cursor: 'pointer'
                  }}
                >
                  {metric}
                </button>
              );
            })}
          </div>
          {(!feat.priority_metrics || feat.priority_metrics.length === 0) && (
            <span style={{ fontSize: '10px', color: '#ff6b6b', display: 'block', marginTop: '5px' }}>
              ⚠️ Selecciona al menos una métrica
            </span>
          )}
        </div>
      )}
    </div>
  );
};

// Estilos necesarios encapsulados
const featureCard: React.CSSProperties = { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333", display: "flex", flexDirection: "column", gap: "10px" };
const featureHeader: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center" };
const featureName: React.CSSProperties = { fontWeight: "bold", color: "#648f8c", fontSize: "16px" };
const selectStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", border: "1px solid #333", borderRadius: "4px", padding: "2px 5px" };
const labelStyle: React.CSSProperties = { fontSize: "12px", color: "#aaa" };
const textAreaStyle: React.CSSProperties = { backgroundColor: "#121212", color: "#ccc", border: "1px solid #333", borderRadius: "8px", padding: "10px", fontSize: "12px", height: "60px", resize: "none" };
const mappingRowStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "#121212", padding: "4px 8px", borderRadius: "4px" };
const mappingInputStyle: React.CSSProperties = { width: "50px", backgroundColor: "#1e1e1e", color: "white", border: "1px solid #333", borderRadius: "4px", padding: "2px", textAlign: "center", fontSize: "12px" };