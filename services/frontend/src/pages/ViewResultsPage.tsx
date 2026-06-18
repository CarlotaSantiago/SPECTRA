import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Target, Percent, Cpu, Sliders, LayoutGrid, CheckCircle } from "lucide-react";

// Colores dinámicos basados en la métrica real (cv_score) devuelta por el JSON
const getScoreColors = (score: number) => {
  if (score >= 0.95) return { color: "#a9dc76", bgColor: "rgba(169, 220, 118, 0.05)" }; // Verde
  if (score >= 0.85) return { color: "#78a8a4", bgColor: "rgba(120, 168, 164, 0.05)" }; // Turquesa
  return { color: "#ffda6a", bgColor: "rgba(255, 218, 106, 0.05)" }; // Amarillo/Ámbar
};

export const ViewResultsPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();

  // 1. Apuntamos a la estructura real de tu JSON del backend
  const targetsData = state?.toonData?.targets || {};
  
  // 2. Convertimos el objeto indexado de "targets" en un array dinámico iterable
  const trainingResults = Object.values(targetsData);

  // 3. Métricas calculadas dinámicamente sobre tu JSON real
  const totalPhases = trainingResults.length;
  
  const avgScore = totalPhases > 0 
    ? trainingResults.reduce((acc: number, curr: any) => acc + (curr.cv_score || 0), 0) / totalPhases 
    : 0;

  if (totalPhases === 0) {
    return (
      <div style={styles.errorStyle}>
        <h2>No se han recibido métricas estructuradas del backend.</h2>
        <button onClick={() => navigate("/")} style={styles.backBtnStyle}>Volver al inicio</button>
      </div>
    );
  }

  return (
    <div style={styles.containerStyle}>
      {/* CABECERA */}
      <div style={styles.headerStyle}>
        <button onClick={() => navigate("/")} style={styles.backBtnStyle}>
          <ArrowLeft size={18} /> Realizar otro entrenamiento
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#648f8c", fontSize: "12px", fontWeight: "bold" }}>
          <CheckCircle size={14} color="#a9dc76" /> PIPELINE FINALIZADO CON ÉXITO
        </div>
      </div>

      {/* SECCIÓN PRINCIPAL */}
      <div style={styles.contentStyle}>
        
        {/* KPI DASHBOARD */}
        <div style={styles.kpiRowStyle}>
          <div style={styles.kpiCardStyle}>
            <Target size={20} color="#648f8c" />
            <div>
              <div style={styles.kpiLabelStyle}>Precisión Media General (CV)</div>
              <div style={{ fontSize: "24px", fontWeight: "bold", color: "#fff" }}>
                {(avgScore * 100).toFixed(2)}%
              </div>
            </div>
          </div>
          
          <div style={styles.kpiCardStyle}>
            <LayoutGrid size={20} color="#648f8c" />
            <div>
              <div style={styles.kpiLabelStyle}>Modelos Procesados</div>
              <div style={{ fontSize: "16px", fontWeight: "bold", color: "#fff", marginTop: "4px" }}>
                {totalPhases} Objetivos en Paralelo
              </div>
            </div>
          </div>
          
          <div style={styles.kpiCardStyle}>
            <Cpu size={20} color="#648f8c" />
            <div>
              <div style={styles.kpiLabelStyle}>Estrategia Optimización</div>
              <div style={{ fontSize: "16px", fontWeight: "bold", color: "#fff", marginTop: "4px" }}>
                Métrica Base: {String(trainingResults[0]?.optimization_metric || "F1").toUpperCase()}
              </div>
            </div>
          </div>
        </div>

        <div style={{ margin: "10px 0 20px 0" }}>
          <h2 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff", margin: 0 }}>Métricas Detalladas por Objetivo</h2>
          <p style={{ fontSize: "12px", color: "#666", margin: "4px 0 0 0" }}>Resultados leídos directamente del reporte persistido en backend</p>
        </div>

        {/* REJILLA DE TARJETAS DE ENTRENAMIENTO DINÁMICAS */}
        <div style={styles.gridStyle}>
          {trainingResults.map((targetItem: any, index: number) => {
            const { color, bgColor } = getScoreColors(targetItem.cv_score || 0);
            
            // Extraemos hiperparámetros excluyendo el meta-campo "model_name" si existe
            const { model_name, ...hyperParams } = targetItem.best_params || {};

            return (
              <div 
                key={targetItem.target || index} 
                style={{ 
                  ...styles.phaseCardStyle, 
                  backgroundColor: bgColor, 
                  borderColor: `${color}22` 
                }}
              >
                {/* Encabezado */}
                <div style={{ marginBottom: "16px" }}>
                  <span style={{ fontSize: "11px", color: "#666", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    Fase {index + 1} • {targetItem.optimization_metric ? `Optimizado por ${targetItem.optimization_metric}` : ""}
                  </span>
                  <h3 style={{ fontSize: "22px", fontWeight: "bold", color: "#fff", margin: "4px 0 0 0", textTransform: "capitalize" }}>
                    {targetItem.target}
                  </h3>
                </div>

                {/* CV Score */}
               {/* Score Visual Destacado */}
              <div style={styles.scoreBoxStyle}>
                <span style={{ fontSize: "12px", color: "#888", fontWeight: "500" }}>Cross-Validation Score</span>
                <span style={{ fontSize: "32px", fontWeight: "900", color: color, display: "flex", alignItems: "center", gap: "2px" }}>
                  {/* Se removió el icono <Percent /> de aquí delante */}
                  {((targetItem.cv_score || 0) * 100).toFixed(2)}%
                </span>
              </div>

                {/* Algoritmo Ganador */}
                <div style={styles.modelRowStyle}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Cpu size={16} color="#648f8c" />
                    <span style={{ fontSize: "13px", color: "#ccc" }}>Algoritmo Ganador:</span>
                  </div>
                  <span style={styles.modelBadgeStyle}>
                    {model_name || "Modelo Asignado"}
                  </span>
                </div>

                {/* Hiperparámetros óptimos */}
                {hyperParams && Object.keys(hyperParams).length > 0 && (
                  <div style={styles.paramsWrapperStyle}>
                    <div style={styles.paramsHeaderStyle}>
                      <Sliders size={12} /> Parámetros de Configuración
                    </div>
                    <div style={styles.badgeGridStyle}>
                      {Object.entries(hyperParams).map(([key, val]: [string, any]) => (
                        <div key={key} style={styles.paramBadgeStyle}>
                          <span style={{ color: "#555" }}>{key}:</span>
                          <span style={{ color: "#aaa", fontWeight: "bold" }}> {val !== null ? val.toString() : "null"}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};

// Se mantienen los mismos estilos premium CSS-in-JS originales
const styles: Record<string, React.CSSProperties> = {
  containerStyle: { backgroundColor: "#0d0d0d", color: "white", height: "calc(100vh - 50px)", padding: "20px", boxSizing: "border-box", overflowY: "auto", fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif" },
  headerStyle: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px", borderBottom: "1px solid #1a1a1a", paddingBottom: "15px" },
  backBtnStyle: { background: "none", border: "none", color: "#648f8c", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", fontWeight: "500" },
  contentStyle: { maxWidth: "1200px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "5px" },
  kpiRowStyle: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "20px", marginBottom: "10px" },
  kpiCardStyle: { backgroundColor: "#141414", border: "1px solid #222", borderRadius: "12px", padding: "20px", display: "flex", alignItems: "center", gap: "16px" },
  kpiLabelStyle: { fontSize: "12px", color: "#666", fontWeight: "600", textTransform: "uppercase" },
  gridStyle: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "25px" },
  phaseCardStyle: { border: "1px solid", borderRadius: "16px", padding: "24px", display: "flex", flexDirection: "column", justifyContent: "space-between", boxShadow: "0 4px 30px rgba(0, 0, 0, 0.4)", backdropFilter: "blur(5px)" },
  scoreBoxStyle: { display: "flex", flexDirection: "column", backgroundColor: "rgba(0,0,0,0.2)", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.03)", marginBottom: "16px" },
  modelRowStyle: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", padding: "0 4px" },
  modelBadgeStyle: { backgroundColor: "#1a1a1a", color: "#fff", fontSize: "12px", fontWeight: "bold", padding: "4px 10px", borderRadius: "6px", border: "1px solid #333" },
  paramsWrapperStyle: { backgroundColor: "#080808", borderRadius: "10px", padding: "14px", border: "1px solid #1a1a1a" },
  paramsHeaderStyle: { fontSize: "11px", color: "#555", fontWeight: "bold", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "6px", marginBottom: "10px" },
  badgeGridStyle: { display: "flex", flexWrap: "wrap", gap: "8px" },
  paramBadgeStyle: { backgroundColor: "#111", fontSize: "11px", padding: "4px 8px", borderRadius: "6px", border: "1px solid #222", fontFamily: "monospace" },
  errorStyle: { backgroundColor: "#121212", color: "white", minHeight: "100vh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "20px" }
};

export default ViewResultsPage;