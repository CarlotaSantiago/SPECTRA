/**
 * @file ViewDataPage.tsx
 * @description Tercera etapa del pipeline. Muestra al usuario los resultados del análisis
 * inicial (State 1), incluyendo sugerencias de orquestación, cardinalidad, validaciones cruzadas,
 * y permite al usuario modificar estas asunciones antes de enviar a generar el script (State 2).
 */

import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Brain, LayoutGrid, Activity } from "lucide-react";
import { ModelPicker } from "../feature/components/ModelPicker";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";
import { LoadingOverlay } from "../feature/components/LoadingOverlay";
import { useData } from "../feature/hooks/useData";
import { OrchestrationPlanViewer } from "../feature/components/OrchestrationPlanViewer";
import { initializeDossierConstraints } from "../feature/hooks/useDefaultConstraints";
import { EvaluationCard } from "../feature/components/EvaluationCard";

const TECHNICAL_LEVEL_MAP: Record<number, string> = {
  0: "Texto / NLP",
  1: "Binario",
  2: "Categórico",
  3: "Numérico",
  4: "Alta Cardinalidad"
};

const METRICS_OPTIONS = {
  CLASSIFICATION: ["F1-Score", "AUC-ROC", "Accuracy", "Precision", "Recall", "Kappa", "Log-Loss"],
  REGRESSION: ["R2-Score", "MAE", "MSE", "RMSE", "MAPE"]
};

/**
 * Página interactiva que renderiza el Dossier recibido del servidor.
 * Administra el estado intermedio de las constraints dictadas por el usuario.
 */
export const ViewDataPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { models: ollamaModels, loading: loadingModels, resolveSelection } = useOllamaModels();
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [selectedModel, setSelectedModel] = useState("");
  
  const { runDeploy, loading } = useData((result) => {
    navigate("/edit-script", {
      state: {
        scriptCode: result.script || result.data?.script,
        toonData: result
      }
    });
  });
  
  const [dossier, setDossier] = useState<any>(() =>
    initializeDossierConstraints(state?.toonData || null)
  );

  if (!dossier) {
    return (
      <div style={errorStyle}>
        <h2>No se encontraron datos del análisis.</h2>
        <button onClick={() => navigate(-1)} style={backBtnStyle}>Volver</button>
      </div>
    );
  }

  const handleUpdateMapping = (featureName: string, keyToUpdate: string, newVal: number) => {
    const feat = dossier.data.targets_evaluation[featureName] || dossier.data.categorical_evaluation[featureName];
    
    const parseMappingInternal = (mappingStr: string) => {
      if (!mappingStr) return {};
      const cleanStr = mappingStr.replace(/[{}]/g, "");
      return cleanStr.split(",").reduce((acc: any, pair) => {
        const [k, v] = pair.split(":").map(s => s.trim());
        if(k) acc[k] = parseInt(v);
        return acc;
      }, {});
    };

    const currentMappingObj = parseMappingInternal(feat.mapping);
    currentMappingObj[keyToUpdate] = newVal;

    const mappingString = `{${Object.entries(currentMappingObj).map(([k, v]) => `${k}: ${v}`).join(", ")}}`;
    const section = dossier.data.targets_evaluation[featureName] ? 'targets_evaluation' : 'categorical_evaluation';

    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        [section]: {
          ...prev.data[section],
          [featureName]: { ...prev.data[section][featureName], mapping: mappingString }
        }
      }
    }));
  };

  const handleUpdateMetrics = (targetName: string, metric: string) => {
    const currentMetrics = dossier.data.targets_evaluation[targetName].priority_metrics || [];
    const newMetrics = currentMetrics.includes(metric)
      ? currentMetrics.filter((m: string) => m !== metric)
      : [...currentMetrics, metric];

    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        targets_evaluation: {
          ...prev.data.targets_evaluation,
          [targetName]: { ...prev.data.targets_evaluation[targetName], priority_metrics: newMetrics }
        }
      }
    }));
  };

  const handleEditFeature = (featureName: string, field: string, value: string) => {
    setDossier((prev: any) => {
      const isTarget = prev.data.targets_evaluation && !!prev.data.targets_evaluation[featureName];
      const section = isTarget ? 'targets_evaluation' : 'categorical_evaluation';
      const extraFields = (field === 'subclass' && value === 'NOMINAL') ? { mapping: "{}" } : {};

      return {
        ...prev,
        data: {
          ...prev.data,
          [section]: {
            ...prev.data[section],
            [featureName]: { ...prev.data[section][featureName], [field]: value, ...extraFields }
          }
        }
      };
    });
  };

  const handleEditStrategy = (newStrategy: string) => {
    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        orchestration_plan: { ...prev.data.orchestration_plan, strategy: newStrategy }
      }
    }));
  };

  const handleUpdateConstraint = (category: string, field: string, value: any) => {
    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        user_constraints: {
          ...prev.data.user_constraints,
          [category]: {
            ...prev.data.user_constraints?.[category],
            [field]: value
          }
        }
      }
    }));
  };

  const moveOrderItem = (index: number, direction: 'up' | 'down') => {
    if (!dossier.data.orchestration_plan.order) return;
    const newOrder = [...dossier.data.orchestration_plan.order];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newOrder.length) return;
    [newOrder[index], newOrder[targetIndex]] = [newOrder[targetIndex], newOrder[index]];

    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        orchestration_plan: { ...prev.data.orchestration_plan, order: newOrder }
      }
    }));
  };

  const handleDeploy = async () => {
    if (!selectedModel) {
      alert("Por favor, selecciona un modelo antes de continuar.");
      setShowModelPicker(true);
      return;
    }

    const { model, provider } = resolveSelection(selectedModel);
    await runDeploy({
      dossier: dossier.data,
      path: dossier.path,
      extension: dossier.extension,
      model,
      ...(provider && { provider }),
    });
  };

  const matrixKeys = dossier?.data?.target_dependency_matrix ? Object.keys(dossier.data.target_dependency_matrix) : [];

  return (
    <div style={containerStyle}>
      {(loading || loadingModels) && <LoadingOverlay message={loadingModels ? "Cargando modelos de IA..." : "Generando script de entreno..."} />}        
        
        <div style={headerStyle}>
        <button onClick={() => navigate(-1)} style={backBtnStyle}><ArrowLeft size={18} /> Volver</button>
        <div style={{ display: 'flex', gap: '10px' }}>
          <ModelPicker 
            allModels={ollamaModels.filter(m => {
              const lower = m.toLowerCase();
              return lower.includes("coder") || lower.includes("mistral") || lower.includes("cursor");
            })}
            selectedModel={selectedModel}
            isOpen={showModelPicker}
            onToggleOpen={() => setShowModelPicker(!showModelPicker)}
            onSelectModel={setSelectedModel}
          />
        </div>
        <button onClick={handleDeploy} style={deployBtnStyle}>
          <Brain size={18} /> Iniciar Generación de Script
        </button>
      </div>

      <div style={contentLayout}>
        {/* Sidebar Izquierda */}
        <div style={sidebarStyle}>
          
        <h2 style={sectionTitle}><Brain size={20}/> Análisis de Orquestación</h2>
          {/* Metadatos */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Activity size={16}/> Metadatos</h3>
            <div style={infoRow}><span>Filas:</span> <strong>{dossier?.data?.global_metadata?.total_rows}</strong></div>
            <div style={infoRow}><span>Muestra:</span> <strong>{dossier?.data?.global_metadata?.sampling_strategy}</strong></div>
          </section>

          {/* Orquestación */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><LayoutGrid size={16}/> Plan de Orquestación</h3>
            <select 
              value={dossier?.data?.orchestration_plan?.strategy} 
              onChange={(e) => handleEditStrategy(e.target.value)}
              style={{...selectStyle, width: '100%', marginBottom: '15px'}}
            >
              <option value="ClassifierChain">ClassifierChain</option>
              <option value="RegressorChain">RegressorChain</option>
              <option value="MultiOutput">MultiOutput</option>
              <option value="HybridChain">HybridChain</option>
              <option value="GatedChain">GatedChain</option>
            </select>

            <div style={orderList}>
              <OrchestrationPlanViewer 
                plan={dossier?.data?.orchestration_plan} 
                onMoveItem={moveOrderItem} 
              />
            </div>
          </section>
          {/* Matriz */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Activity size={16}/> Matriz de Dependencia</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={matrixTableStyle}>
                <thead>
                  <tr>
                    <th style={matrixHeaderStyle}></th>
                    {matrixKeys.map(k => <th key={k} style={matrixHeaderStyle}>{k[0].toUpperCase()}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {matrixKeys.map(rowKey => (
                    <tr key={rowKey}>
                      <td style={matrixRowLabelStyle}>{rowKey}</td>
                      {matrixKeys.map(colKey => {
                        const val = dossier.data.target_dependency_matrix[rowKey][colKey];
                        return (
                          <td key={colKey} style={{...matrixCellStyle, color: val > 0 ? '#648f8c' : '#444'}}>
                            {val.toFixed(4)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
        
        {/* Panel Central con Tarjetas Reutilizables */}
        <div style={mainPanelStyle}>
          <h2 style={sectionTitle}><Brain size={20}/> Análisis de Variables Objetivo</h2>
          <div style={gridFeatures}>
            {Object.keys(dossier?.data?.targets_evaluation || {}).map((key) => (
              <EvaluationCard 
                key={key}
                name={key}
                feat={dossier.data.targets_evaluation[key]}
                isTarget={true}
                technicalMap={TECHNICAL_LEVEL_MAP}
                metricOptions={METRICS_OPTIONS.CLASSIFICATION}
                onEditField={handleEditFeature}
                onUpdateMapping={handleUpdateMapping}
                onUpdateMetrics={handleUpdateMetrics}
              />
            ))}
          </div>
            
          <h2 style={sectionTitle}><Brain size={20}/> Análisis Semántico</h2>
          <div style={gridFeatures}>
            {Object.keys(dossier?.data?.categorical_evaluation || {}).map((key) => (
              <EvaluationCard 
                key={key}
                name={key}
                feat={dossier.data.categorical_evaluation[key]}
                isTarget={false}
                technicalMap={TECHNICAL_LEVEL_MAP}
                metricOptions={[]}
                onEditField={handleEditFeature}
                onUpdateMapping={handleUpdateMapping}
              />
            ))}
          </div>

          {/* Variables de Sólo Lectura */}
          {dossier?.data?.classified_evaluation && Object.keys(dossier.data.classified_evaluation).length > 0 && (
            <>
              <h2 style={{...sectionTitle, marginTop: '40px'}}><Activity size={20}/> Análisis Técnico</h2>
              <div style={gridFeatures}>
                {Object.keys(dossier.data.classified_evaluation).map((key) => {
                  const feat = dossier.data.classified_evaluation[key];
                  return (
                    <div key={key} style={{...featureCard, opacity: 0.9, borderStyle: 'dashed'}}>
                      <div style={featureHeader}>
                        <span style={featureName}>{key}</span>
                        <span style={badge}>{feat.subclass || "TÉCNICO"}</span>
                      </div>
                      <div style={{marginTop: '10px'}}>
                        <div style={infoRow}>
                          <span>Tipo de Dato:</span> 
                          <strong style={{color: '#648f8c'}}>{TECHNICAL_LEVEL_MAP[feat.technical_level] || feat.technical_level}</strong>
                        </div>
                        <div style={infoRow}>
                          <span>Obligatorio:</span> <strong>{feat.user_mandatory ? "SÍ" : "NO"}</strong>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Sidebar Derecha */}
        <div style={sidebarStyle}>
          {/* Parámetros de Entrenamiento */}
          <h2 style={sectionTitle}><Brain size={20}/> Métricas que se desean usar</h2>
          <section style={cardStyle}>
            <h3 style={cardTitle}><Brain size={16}/> Configuración de Entrenamiento</h3>
            
            <div style={{ marginBottom: "12px" }}>
              <div style={infoRow}>
                <span>CV Folds:</span>
                <strong style={{color: '#648f8c'}}>{dossier?.data?.user_constraints?.cv_strategy?.folds || 5}</strong>
              </div>
              <input
                type="range"
                min={1}
                max={20}
                value={dossier?.data?.user_constraints?.cv_strategy?.folds || 10}
                onChange={(e) => handleUpdateConstraint('cv_strategy', 'folds', parseInt(e.target.value))}
                style={{ width: "100%", accentColor: "#648f8c" }}
              />
            </div>

            <div style={{ marginBottom: "12px" }}>
              <div style={infoRow}>
                <span>Max Trials (Optuna):</span>
                <strong style={{color: '#648f8c'}}>{dossier?.data?.user_constraints?.tuning_strategy?.max_trials || 50}</strong>
              </div>
              <input
                type="number"
                min={1}
                max={1000}
                value={dossier?.data?.user_constraints?.tuning_strategy?.max_trials ?? 50}
                onChange={(e) => handleUpdateConstraint('tuning_strategy', 'max_trials', e.target.value === '' ? '' : parseInt(e.target.value))}
                style={{ ...selectStyle, width: "100%", boxSizing: "border-box" }}
              />
            </div>

            <div>
              <div style={infoRow}>
                <span>Timeout (Minutos):</span>
                <strong style={{color: '#648f8c'}}>{dossier?.data?.user_constraints?.tuning_strategy?.timeout || 30}</strong>
              </div>
              <input
                type="number"
                min={0}
                max={1440}
                value={dossier?.data?.user_constraints?.tuning_strategy?.timeout ?? 30}
                onChange={(e) => handleUpdateConstraint('tuning_strategy', 'timeout', e.target.value === '' ? '' : parseInt(e.target.value))}
                style={{ ...selectStyle, width: "100%", boxSizing: "border-box" }}
              />
            </div>
          </section>
          {/* CARD: Resumen de configuración */}
                    <section style={cardStyle}>
                      <h3 style={styles.cardTitleStyle}>
                        <LayoutGrid size={16} /> Resumen de Ejecución
                      </h3>
                      <div style={styles.summaryRowStyle}>
                        <span style={styles.labelStyle}>Folds CV:</span>
                        <span style={styles.valueBadgeStyle}>{dossier?.data?.user_constraints?.cv_strategy?.folds || 5}</span>
                      </div>
                      <div style={styles.summaryRowStyle}>
                        <span style={styles.labelStyle}>Max Trials:</span>
                        <span style={styles.valueBadgeStyle}>{dossier?.data?.user_constraints?.tuning_strategy?.max_trials || 50}</span>
                      </div>
                      <div style={styles.summaryRowStyle}>
                        <span style={styles.labelStyle}>Timeout:</span>
                        <span style={styles.valueBadgeStyle}>{dossier?.data?.user_constraints?.tuning_strategy?.timeout || 30} min</span>
                      </div>
                    </section>
        </div>
      </div>
    </div>
  );
};

const containerStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", minHeight: "100vh", padding: "20px", fontFamily: "sans-serif", overflowX: "auto" };
const headerStyle: React.CSSProperties = { display: "flex", justifyContent: "space-between", marginBottom: "20px" };
const contentLayout: React.CSSProperties = { display: "grid", gridTemplateColumns: "300px 1fr 300px", gap: "20px", alignItems: "start" };
const sidebarStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "20px", position: "sticky", top: "20px" };
const mainPanelStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "15px" };
const cardStyle: React.CSSProperties = { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333" };
const cardTitle: React.CSSProperties = { color: "#648f8c", fontSize: "14px", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" };
const sectionTitle: React.CSSProperties = { fontSize: "18px", color: "white", display: "flex", alignItems: "center", gap: "10px", marginTop: "10px" };
const gridFeatures: React.CSSProperties = { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "15px" };
const infoRow: React.CSSProperties = { display: "flex", justifyContent: "space-between", fontSize: "13px", color: "#aaa", marginBottom: "5px" };
const backBtnStyle: React.CSSProperties = { background: "none", border: "none", color: "#648f8c", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" };
const selectStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", border: "1px solid #333", borderRadius: "4px", padding: "2px 5px" };
const orderList: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "4px" };
const matrixTableStyle: React.CSSProperties = { width: "100%", borderCollapse: "collapse", marginTop: "10px", fontSize: "11px" };
const matrixHeaderStyle: React.CSSProperties = { padding: "4px", textAlign: "center", color: "#648f8c", borderBottom: "1px solid #333" };
const matrixRowLabelStyle: React.CSSProperties = { padding: "4px", color: "#aaa", borderRight: "1px solid #333", textAlign: "left" };
const matrixCellStyle: React.CSSProperties = { padding: "4px", textAlign: "center", borderBottom: "1px solid #222" };
const errorStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100vh" };
const featureCard: React.CSSProperties = { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333", display: "flex", flexDirection: "column", gap: "10px" };
const featureHeader: React.CSSProperties = { display: "flex", justifyContent: "space-between", alignItems: "center" };
const featureName: React.CSSProperties = { fontWeight: "bold", color: "#648f8c", fontSize: "16px" };
const badge: React.CSSProperties = { backgroundColor: "#648f8c33", color: "#648f8c", padding: "4px 10px", borderRadius: "12px", fontSize: "12px" };
const deployBtnStyle: React.CSSProperties = { backgroundColor: "#648f8c", color: "white", border: "none", padding: "10px 20px", borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontWeight: "bold", boxShadow: "0 4px 14px 0 rgba(100, 143, 140, 0.39)" };

const styles: Record<string, React.CSSProperties> = {
summaryRowStyle: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "8px",
  },
  valueBadgeStyle: {
    backgroundColor: "#1a3330",
    color: "#648f8c",
    borderRadius: "6px",
    padding: "2px 10px",
    fontSize: "13px",
    fontWeight: "bold",
    border: "1px solid #648f8c",
  },
  cardTitleStyle: {
    color: "#648f8c",
    fontSize: "13px",
    marginTop: 0,
    marginBottom: "12px",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  labelStyle: {
    display: "block",
    fontSize: "11px",
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
    color: "#648f8c",
    fontWeight: "bold",
    marginBottom: "4px",
    marginTop: "8px",
  },
};
export default ViewDataPage;