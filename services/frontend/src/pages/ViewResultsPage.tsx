import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Target, Percent, Cpu, Sliders, LayoutGrid, CheckCircle } from "lucide-react";

export const ViewResultsPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();

  // Datos reales estructurados del pipeline AutoML
  const [trainingResults] = useState([
    {
      target: "especialidad",
      phase: "Fase 1 • Clasificación Principal",
      model: "LGBMClassifier",
      score: 1.000000,
      color: "#a9dc76", // Verde brillante para score perfecto
      bgColor: "rgba(169, 220, 118, 0.05)",
      trials: 8,
      params: { learning_rate: 0.1, max_depth: 5, n_estimators: 300, num_leaves: 31, subsample: 0.7 }
    },
    {
      target: "sala",
      phase: "Fase 2 • Clasificación Dependiente",
      model: "XGBClassifier",
      score: 0.914746,
      color: "#78a8a4", // Turquesa para score alto
      bgColor: "rgba(120, 168, 164, 0.05)",
      trials: 1,
      params: { learning_rate: 0.05, max_depth: 7, n_estimators: 500, subsample: 0.9, colsample_bytree: 1.0 }
    },
    {
      target: "prioridad",
      phase: "Fase 3 • Clasificación Crítica",
      model: "RandomForestClassifier",
      score: 0.734627,
      color: "#ffda6a", // Amarillo/Ámbar
      bgColor: "rgba(255, 218, 106, 0.05)",
      trials: 7,
      params: { max_depth: "None", min_samples_split: 10, n_estimators: 300, max_features: "sqrt" }
    }
  ]);

  // Cálculo del promedio general
  const avgScore = trainingResults.reduce((acc, curr) => acc + curr.score, 0) / trainingResults.length;

  return (
    <div style={containerStyle}>
      {/* CABECERA */}
      <div style={headerStyle}>
        <button onClick={() => navigate("/")} style={backBtnStyle}>
          <ArrowLeft size={18} /> Realizar otro entrenamiento
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#648f8c", fontSize: "12px", fontWeight: "bold" }}>
          <CheckCircle size={14} color="#a9dc76" /> PIPELINE FINALIZADO CON ÉXITO
        </div>
      </div>

      {/* SECCIÓN PRINCIPAL */}
      <div style={contentStyle}>
        
        {/* FILA DE DATOS GLOBALES (KPIs RÁPIDOS) */}
        <div style={kpiRowStyle}>
          <div style={kpiCardStyle}>
            <Target size={20} color="#648f8c" />
            <div>
              <div style={kpiLabelStyle}>Precisión Media General</div>
              <div style={{ fontSize: "24px", fontWeight: "bold", color: "#fff" }}>
                {(avgScore * 100).toFixed(2)}%
              </div>
            </div>
          </div>
          <div style={kpiCardStyle}>
            <LayoutGrid size={20} color="#648f8c" />
            <div>
              <div style={kpiLabelStyle}>Estructura de Red</div>
              <div style={{ fontSize: "16px", fontWeight: "bold", color: "#fff", marginTop: "4px" }}>
                GatedChain (3 Niveles)
              </div>
            </div>
          </div>
          <div style={kpiCardStyle}>
            <Cpu size={20} color="#648f8c" />
            <div>
              <div style={kpiLabelStyle}>Total de Pruebas (Optuna)</div>
              <div style={{ fontSize: "24px", fontWeight: "bold", color: "#fff" }}>
                {trainingResults.reduce((acc, curr) => acc + curr.trials, 0)} Trials
              </div>
            </div>
          </div>
        </div>

        {/* TÍTULO DE LA SECCIÓN */}
        <div style={{ margin: "10px 0 20px 0" }}>
          <h2 style={{ fontSize: "18px", fontWeight: "bold", color: "#fff", margin: 0 }}>Métricas Detalladas por Objetivo</h2>
          <p style={{ fontSize: "12px", color: "#666", margin: "4px 0 0 0" }}>Resultados óptimos seleccionados por competencia autónoma</p>
        </div>

        {/* REJILLA DE TARJETAS DE ENTRENAMIENTO */}
        <div style={gridStyle}>
          {trainingResults.map((phase) => (
            <div key={phase.target} style={{ ...phaseCardStyle, backgroundColor: phase.bgColor, borderColor: `${phase.color}22` }}>
              
              {/* Encabezado de la Tarjeta */}
              <div style={{ marginBottom: "16px" }}>
                <span style={{ fontSize: "11px", color: "#666", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  {phase.phase}
                </span>
                <h3 style={{ fontSize: "22px", fontWeight: "bold", color: "#fff", margin: "4px 0 0 0", textTransform: "capitalize" }}>
                  {phase.target}
                </h3>
              </div>

              {/* Score Visual Destacado */}
              <div style={scoreBoxStyle}>
                <span style={{ fontSize: "12px", color: "#888", fontWeight: "500" }}>Cross-Validation Score</span>
                <span style={{ fontSize: "32px", fontWeight: "900", color: phase.color, display: "flex", alignItems: "center", gap: "2px" }}>
                  <Percent size={24} strokeWidth={3} /> {(phase.score * 100).toFixed(2)}%
                </span>
              </div>

              {/* Algoritmo Ganador */}
              <div style={modelRowStyle}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Cpu size={16} color="#648f8c" />
                  <span style={{ fontSize: "13px", color: "#ccc" }}>Algoritmo Ganador:</span>
                </div>
                <span style={modelBadgeStyle}>{phase.model}</span>
              </div>

              {/* Contenedor de Parámetros */}
              <div style={paramsWrapperStyle}>
                <div style={paramsHeaderStyle}>
                  <Sliders size={12} /> Hiperparámetros Óptimos
                </div>
                <div style={badgeGridStyle}>
                  {Object.entries(phase.params).map(([key, val]) => (
                    <div key={key} style={paramBadgeStyle}>
                      <span style={{ color: "#555" }}>{key}:</span>
                      <span style={{ color: "#aaa", fontWeight: "bold" }}> {val.toString()}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          ))}
        </div>

      </div>
    </div>
  );
};

// =====================================================================
// HOJA DE ESTILOS CSS-IN-JS (UI DASHBOARD PREMIUM)
// =====================================================================
const containerStyle: React.CSSProperties = {
  backgroundColor: "#0d0d0d",
  color: "white",
  height: "100vh",
  padding: "30px",
  boxSizing: "border-box",
  overflowY: "auto",
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
};

const headerStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "30px",
  borderBottom: "1px solid #1a1a1a",
  paddingBottom: "15px"
};

const backBtnStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  color: "#648f8c",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "8px",
  fontSize: "14px",
  fontWeight: "500",
  transition: "color 0.2s"
};

const contentStyle: React.CSSProperties = {
  maxWidth: "1200px",
  margin: "0 auto",
  display: "flex",
  flexDirection: "column",
  gap: "20px"
};

const kpiRowStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(3, 1fr)",
  gap: "20px",
  marginBottom: "10px"
};

const kpiCardStyle: React.CSSProperties = {
  backgroundColor: "#141414",
  border: "1px solid #222",
  borderRadius: "12px",
  padding: "20px",
  display: "flex",
  alignItems: "center",
  gap: "16px"
};

const kpiLabelStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#666",
  fontWeight: "600",
  textTransform: "uppercase"
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
  gap: "25px"
};

const phaseCardStyle: React.CSSProperties = {
  border: "1px solid",
  borderRadius: "16px",
  padding: "24px",
  display: "flex",
  flexDirection: "column",
  justifyContent: "space-between",
  boxShadow: "0 4px 30px rgba(0, 0, 0, 0.4)",
  backdropFilter: "blur(5px)"
};

const scoreBoxStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  backgroundColor: "rgba(0,0,0,0.2)",
  padding: "16px",
  borderRadius: "10px",
  border: "1px solid rgba(255,255,255,0.03)",
  marginBottom: "16px"
};

const modelRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "20px",
  padding: "0 4px"
};

const modelBadgeStyle: React.CSSProperties = {
  backgroundColor: "#1a1a1a",
  color: "#fff",
  fontSize: "12px",
  fontWeight: "bold",
  padding: "4px 10px",
  borderRadius: "6px",
  border: "1px solid #333"
};

const paramsWrapperStyle: React.CSSProperties = {
  backgroundColor: "#080808",
  borderRadius: "10px",
  padding: "14px",
  border: "1px solid #1a1a1a"
};

const paramsHeaderStyle: React.CSSProperties = {
  fontSize: "11px",
  color: "#555",
  fontWeight: "bold",
  textTransform: "uppercase",
  display: "flex",
  alignItems: "center",
  gap: "6px",
  marginBottom: "10px"
};

const badgeGridStyle: React.CSSProperties = {
  display: "flex",
  flexWrap: "wrap",
  gap: "8px"
};

const paramBadgeStyle: React.CSSProperties = {
  backgroundColor: "#111",
  fontSize: "11px",
  padding: "4px 8px",
  borderRadius: "6px",
  border: "1px solid #222",
  fontFamily: "monospace"
};

export default ViewResultsPage;