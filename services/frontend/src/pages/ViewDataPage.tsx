import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Save, Brain, LayoutGrid, Activity, ChevronUp, ChevronDown } from "lucide-react";
import { ModelPicker } from "../feature/components/ModelPicker";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";


// =====================================================================
// COMPONENTE AUXILIAR PARA RENDERIZAR LA ORQUESTACIÓN (Soporta GatedChain)
// =====================================================================
const OrchestrationPlanViewer = ({ plan, onMoveItem }: { plan: any; onMoveItem: (idx: number, dir: 'up' | 'down') => void }) => {
  if (!plan) return null;

  const { strategy, order, gating, dependents, sub_strategy } = plan;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Badge con el nombre de la estrategia actual */}
      <div style={{ fontSize: '11px', color: '#648f8c', fontWeight: 'bold', textTransform: 'uppercase', marginBottom: '2px' }}>
        Estrategia: {strategy}
      </div>

      {/* CASO A: Estrategias normales con orden secuencial plano */}
      {order && order.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {order.map((target: string, i: number) => (
            <div key={target} style={orderItemEditable}>
              <span>{i + 1}. {target}</span>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button 
                  onClick={() => onMoveItem(i, 'up')} 
                  disabled={i === 0}
                  style={miniBtnStyle}
                >
                  <ChevronUp size={14}/>
                </button>
                <button 
                  onClick={() => onMoveItem(i, 'down')} 
                  disabled={i === order.length - 1}
                  style={miniBtnStyle}
                >
                  <ChevronDown size={14}/>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CASO B: Estructura GatedChain (Ausencias Estructurales) */}
      {strategy === "GatedChain" && (
        <div style={{ borderLeft: '2px dashed #ff6b6b', paddingLeft: '10px', marginTop: '4px' }}>
          {/* Nodo de bloqueo */}
          <div style={{ ...orderItemEditable, borderLeft: '3px solid #ff6b6b', backgroundColor: '#1a1212' }}>
            <span style={{ color: '#ff6b6b' }}>🛑 Variable Condicional: <strong>{gating}</strong></span>
          </div>

          {/* Indicador de variables subordinadas */}
          <div style={{ fontSize: '11px', color: '#aaa', margin: '6px 0 4px 4px' }}>
            👇 Dependientes directos (Si {gating} está presente):
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '10px', paddingLeft: '4px' }}>
            {dependents?.map((dep: string) => (
              <span key={dep} style={{ fontSize: '11px', backgroundColor: '#222', color: '#ccc', padding: '3px 8px', borderRadius: '4px', border: '1px solid #333' }}>
                {dep}
              </span>
            ))}
          </div>

          {/* Sub-estrategia anidada (Llamada recursiva) */}
          {sub_strategy && (
            <div style={{ marginTop: '10px', backgroundColor: 'rgba(255,255,255,0.02)', padding: '8px', borderRadius: '6px' }}>
              <OrchestrationPlanViewer plan={sub_strategy} onMoveItem={onMoveItem} />
            </div>
          )}
        </div>
      )}

      {/* Fallback si no hay datos procesables en este nodo */}
      {!order && strategy !== "GatedChain" && (
        <div style={{ padding: '8px', color: '#666', fontStyle: 'italic', textAlign: 'center' }}>
          No hay un orden secuencial definido en este nivel.
        </div>
      )}
    </div>
  );
};

const ViewDataPage = () => {
  // Dentro de ViewDataPage, al recibir el state o inicializar:
  const { state } = useLocation();
  const navigate = useNavigate();
  const { models: ollamaModels, loading: loadingModels, resolveSelection } = useOllamaModels();
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [selectedModel, setSelectedModel] = useState(""); // <-- 2. Estado del modelo
  
  const [dossier, setDossier] = useState<any>(() => {
    const base = state?.toonData || null;
    if (base && !base.data.user_constraints) {
      // Inyectamos los valores predeterminados que pidió el profe
      base.data.user_constraints = {
        cv_strategy: { type: "StratifiedKFold", folds: 10 },
        feature_selection_threshold: 0.05,
        allow_ensembles: true,
        optimization_priority: ["Performance", "Interpretability"],
        model_selection: {
          mode: "AUTONOMOUS_COMPETITION",
          libraries: ["scikit-learn", "xgboost", "lightgbm"]
        },
        tuning_strategy: {
          search_type: "Bayesian_Optimization",
          max_trials: 50,
          timeout: 600
        }
      };
    }
    return base;
  });
  if (!dossier) {
    return (
      <div style={errorStyle}>
        <h2>No se encontraron datos del análisis.</h2>
        <button onClick={() => navigate(-1)} style={backBtnStyle}>Volver</button>
      </div>
    );
  }

  // --- MANEJADORES DE EDICIÓN ---

  const TECHNICAL_LEVEL_MAP: Record<number, string> = {
  0: "Texto / NLP", // Añadido por si acaso
  1: "Binario",
  2: "Categórico",
  3: "Numérico",
  4: "Alta Cardinalidad"
};

const METRICS_OPTIONS = {
  CLASSIFICATION: ["F1-Score", "AUC-ROC", "Accuracy", "Precision", "Recall", "Kappa", "Log-Loss"],
  REGRESSION: ["R2-Score", "MAE", "MSE", "RMSE", "MAPE"]
};

  const handleUpdateConstraint = (field: string, value: any) => {
    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        user_constraints: {
          ...prev.data.user_constraints,
          [field]: value
        }
      }
    }));
  };

  const handleUpdateCV = (field: string, value: any) => {
    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        user_constraints: {
          ...prev.data.user_constraints,
          cv_strategy: { ...prev.data.user_constraints.cv_strategy, [field]: value }
        }
      }
    }));
  };
  // Función para convertir "{A: 0, B: 1}" en [{key: "A", val: 0}, {key: "B", val: 1}]
  const parseMapping = (mappingStr: any) => {
    if (!mappingStr || typeof mappingStr !== "string") return [];
    try {
      // Limpiamos los caracteres de objeto y dividimos por comas
      const cleanStr = mappingStr.replace(/[{}]/g, "");
      return cleanStr.split(",").map(pair => {
        const [key, val] = pair.split(":").map(s => s.trim());
        return { key, val: parseInt(val) };
      }).sort((a, b) => a.val - b.val); // Ordenar por el valor numérico
    } catch (e) {
      return [];
    }
  };
  const handleUpdateMapping = (featureName: string, keyToUpdate: string, newVal: number) => {
  const feat = dossier.data.targets_evaluation[featureName] || dossier.data.categorical_evaluation[featureName];
  const currentMapping = parseMapping(feat.mapping);
  
  // Creamos el nuevo objeto actualizado
  const newMappingObj = currentMapping.reduce((acc: any, item) => {
    acc[item.key] = item.key === keyToUpdate ? newVal : item.val;
    return acc;
  }, {});

  // Lo convertimos de nuevo a string formato "{A: 0, B: 1}"
  const mappingString = `{${Object.entries(newMappingObj).map(([k, v]) => `${k}: ${v}`).join(", ")}}`;

  // Determinamos si es target o feature para actualizar el estado
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
  let newMetrics;
  
  if (currentMetrics.includes(metric)) {
    // Si ya existe, la quitamos (deseleccionar)
    newMetrics = currentMetrics.filter((m: string) => m !== metric);
  } else {
    // Si no existe, la añadimos
    newMetrics = [...currentMetrics, metric];
  }

  setDossier((prev: any) => ({
    ...prev,
    data: {
      ...prev.data,
      targets_evaluation: {
        ...prev.data.targets_evaluation,
        [targetName]: { 
          ...prev.data.targets_evaluation[targetName], 
          priority_metrics: newMetrics 
        }
      }
    }
  }));
};
  const handleEditFeature = (featureName: string, field: string, value: string) => {
    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        categorical_evaluation: {
          ...prev.data.categorical_evaluation,
          [featureName]: { ...prev.data.categorical_evaluation[featureName], [field]: value }
        }
      }
    }));
  };

  // Cambiar estrategia (AUTO/MANUAL/etc)
  const handleEditStrategy = (newStrategy: string) => {
    setDossier((prev: any) => ({
      ...prev,
      data: {
        ...prev.data,
        orchestration_plan: { ...prev.data.orchestration_plan, strategy: newStrategy }
      }
    }));
  };

  // Mover items en el plan de orquestación
  const moveOrderItem = (index: number, direction: 'up' | 'down') => {
    const newOrder = [...dossier.data.orchestration_plan.order];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newOrder.length) return;

    // Swap
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
    const payload = {
      dossier: dossier.data, // Los datos editados (incluyendo mappings y orden)
      path: dossier.path,
      extension: dossier.extension,
      model,
      ...(provider && { provider }),
    };
    console.log("Payload a enviar:", payload);
    try {
      const response = await fetch("http://localhost:8000/process-state2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        alert("Configuración enviada con éxito. Iniciando entrenamiento...");
        console.log("Respuesta del backend:", result);
        // navigate("/training-progress"); // Opcional: Redirigir a una pantalla de carga
      } else {
        throw new Error("Error en la respuesta del servidor");
      }
    } catch (error) {
      console.error("Error al enviar al backend:", error);
      alert("No se pudo conectar con el servidor.");
    }
  };
  const handleSave = () => {
    console.log("Dossier Final:", dossier);
    alert("Dossier actualizado y listo para Etapa 2");
  };

  const matrixKeys = dossier?.data?.target_dependency_matrix ? Object.keys(dossier.data.target_dependency_matrix) : [];

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <button onClick={() => navigate(-1)} style={backBtnStyle}><ArrowLeft size={18} /> Volver</button>
        <div style={{ display: 'flex', gap: '10px' }}>
                  <ModelPicker 
                    allModels={ollamaModels}
                    selectedModel={selectedModel}
                    isOpen={showModelPicker} // Necesitas un nuevo useState [showModelPicker, setShowModelPicker]
                    onToggleOpen={() => setShowModelPicker(!showModelPicker)}
                    onSelectModel={setSelectedModel}/>
        </div>
        {/* Botón de Enviar a Backend */}
        <button onClick={handleDeploy} style={deployBtnStyle}>
          <Brain size={18} /> Iniciar Entrenamiento
        </button>
      </div>

      <div style={contentLayout}>
        <div style={sidebarStyle}>
          {/* Metadatos */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Activity size={16}/> Metadatos</h3>
            <div style={infoRow}><span>Filas:</span> <strong>{dossier?.data?.global_metadata?.total_rows}</strong></div>
            <div style={infoRow}><span>Muestra:</span> <strong>{dossier?.data?.global_metadata?.sampling_strategy}</strong></div>
          </section>

          {/* ORQUESTACIÓN EDITABLE */}
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

            {/* CONTENEDOR DINÁMICO RECURSIVO */}
            <div style={orderList}>
              <OrchestrationPlanViewer 
                plan={dossier?.data?.orchestration_plan} 
                onMoveItem={moveOrderItem} 
              />
            </div>
            <div style={orderList}>
              {dossier?.data?.orchestration_plan?.order && dossier.data.orchestration_plan.order.length > 0 ? (
                dossier.data.orchestration_plan.order.map((target: string, i: number) => (
                  <div key={target} style={orderItemEditable}>
                    <span>{i + 1}. {target}</span>
                    <div style={{display: 'flex', gap: '4px'}}>
                      <button 
                        onClick={() => moveOrderItem(i, 'up')} 
                        disabled={i === 0}
                        style={miniBtnStyle}
                      >
                        <ChevronUp size={14}/>
                      </button>
                      <button 
                        onClick={() => moveOrderItem(i, 'down')} 
                        disabled={i === dossier.data.orchestration_plan.order.length - 1}
                        style={miniBtnStyle}
                      >
                        <ChevronDown size={14}/>
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                // Mensaje que se mostrará si 'order' es undefined, null o está vacío
                <div style={{ padding: '8px', color: '#666', fontStyle: 'italic', textAlign: 'center' }}>
                  No hay un orden secuencial (Estrategia Condicional / GatedChain)
                </div>
              )}
            </div>
          </section>

          {/* MATRIZ DE DEPENDENCIA */}
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
        
        <div style={mainPanelStyle}>
          {/* SECCIÓN 1: TARGETS CATEGÓRICAS (EDITABLES) */}
          <h2 style={sectionTitle}><Brain size={20}/> Análisis de Variables Objetivo</h2>
          <div style={gridFeatures}>
            {Object.keys(dossier?.data?.targets_evaluation || {}).map((key) => {
              const feat = dossier.data.targets_evaluation[key];
              return (
                <div key={key} style={featureCard}>
                  <div style={featureHeader}>
                    <span style={featureName}>{key}</span>
                    <select 
                      value={feat.subclass} 
                      onChange={(e) => handleEditFeature(key, 'subclass', e.target.value)} 
                      style={selectStyle}
                    >
                      <option value="NOMINAL">NOMINAL</option>
                      <option value="ORDINAL">ORDINAL</option>
                      <option value="BINARY">BINARY</option>
                      <option value="TEXT_NLP">TEXT_NLP</option>
                    </select>
                  </div>
                  <label style={labelStyle}>Razonamiento Semántico:</label>
                  <textarea 
                    style={textAreaStyle} 
                    value={feat.reasoning || ""} 
                    onChange={(e) => handleEditFeature(key, 'reasoning', e.target.value)} 
                  />
                  <div style={infoRow}>
                    <span>Tipo Técnico:</span> 
                    <strong style={{color: '#648f8c'}}>
                      {TECHNICAL_LEVEL_MAP[feat.technical_level] || "Desconocido"}
                    </strong>
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
                            onChange={(e) => handleUpdateMapping(key, item.key, parseInt(e.target.value))}
                            style={mappingInputStyle}
                          />
                        </div>
                      </div>
                    ))}
                    {parseMapping(feat.mapping).length === 0 && (
                      <span style={{ fontSize: '11px', color: '#666', fontStyle: 'italic' }}>Sin mapeo definido (Nominal)</span>
                    )}
                    {/* --- SECCIÓN DE MÉTRICAS DENTRO DE LA TARJETA --- */}
                    <div style={{ marginTop: '10px', borderTop: '1px solid #333', paddingTop: '10px' }}>
                      <label style={labelStyle}>Métricas de Prioridad:</label>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '8px' }}>
                        {METRICS_OPTIONS.CLASSIFICATION.map((metric) => {
                          const isSelected = feat.priority_metrics?.includes(metric);
                          return (
                            <button
                              key={metric}
                              onClick={() => handleUpdateMetrics(key, metric)}
                              style={{
                                ...miniBtnStyle,
                                padding: '4px 8px',
                                fontSize: '10px',
                                backgroundColor: isSelected ? '#648f8c' : '#121212',
                                color: isSelected ? 'white' : '#648f8c',
                                border: `1px solid ${isSelected ? '#648f8c' : '#333'}`,
                                transition: 'all 0.2s'
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
                  </div>
                  </div>
                </div>
                
              );
            })}
          </div>
          {/* SECCIÓN 1: VARIABLES CATEGÓRICAS (EDITABLES) */}
          <h2 style={sectionTitle}><Brain size={20}/> Análisis Semántico </h2>
          <div style={gridFeatures}>
            {Object.keys(dossier?.data?.categorical_evaluation || {}).map((key) => {
              const feat = dossier.data.categorical_evaluation[key];
              return (
                <div key={key} style={featureCard}>
                  <div style={featureHeader}>
                    <span style={featureName}>{key}</span>
                    <select 
                      value={feat.subclass} 
                      onChange={(e) => handleEditFeature(key, 'subclass', e.target.value)} 
                      style={selectStyle}
                    >
                      <option value="NOMINAL">NOMINAL</option>
                      <option value="ORDINAL">ORDINAL</option>
                      <option value="BINARY">BINARY</option>
                      <option value="TEXT_NLP">TEXT_NLP</option>
                    </select>
                  </div>
                  <label style={labelStyle}>Razonamiento Semántico:</label>
                  <textarea 
                    style={textAreaStyle} 
                    value={feat.reasoning || ""} 
                    onChange={(e) => handleEditFeature(key, 'reasoning', e.target.value)} 
                  />
                  <div style={infoRow}>
                    <span>Tipo Técnico:</span> 
                    <strong style={{color: '#648f8c'}}>
                      {TECHNICAL_LEVEL_MAP[feat.technical_level] || "Desconocido"}
                    </strong>
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
                            onChange={(e) => handleUpdateMapping(key, item.key, parseInt(e.target.value))}
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
                </div>
              );
            })}
          </div>

          {/* SECCIÓN 2: VARIABLES CLASIFICADAS (SÓLO LECTURA) */}
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
                          <strong style={{color: '#648f8c'}}>
                            {TECHNICAL_LEVEL_MAP[feat.technical_level] || feat.technical_level}
                          </strong>
                        </div>
                        <div style={infoRow}>
                          <span>Obligatorio:</span> 
                          <strong>{feat.user_mandatory ? "SÍ" : "NO"}</strong>
                        </div>
                      </div>

                      {/* Pool de valores simplificado */}
                      <div style={{marginTop: '5px'}}>
                        <label style={{...labelStyle, fontSize: '10px'}}>Muestra de valores:</label>
                        <div style={{display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '5px'}}>
                          {feat.unique_pool?.slice(0, 3).map((v: any, idx: number) => (
                            <span key={idx} style={{fontSize: '10px', color: '#666', backgroundColor: '#121212', padding: '2px 6px', borderRadius: '4px'}}>
                              {String(v)}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
        <div style={sidebarStyle}>
          <h2 style={sectionTitle}><Save size={18}/> Ajustes de Entrenamiento</h2>
          
          {/* CARD: VALIDACIÓN CRUZADA */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Activity size={16}/> Validación Cruzada (CV)</h3>
            <label style={labelStyle}>Estrategia:</label>
            <select 
              value={dossier.data.user_constraints.cv_strategy.type}
              onChange={(e) => handleUpdateCV("type", e.target.value)}
              style={{...selectStyle, width: '100%', marginTop: '5px'}}
            >
              <option value="KFold">KFold (Regresión)</option>
              <option value="StratifiedKFold">StratifiedKFold (Clasificación)</option>
              <option value="ShuffleSplit">ShuffleSplit (Aleatorio)</option>
              <option value="TimeSeriesSplit">TimeSeriesSplit (Temporal)</option>
            </select>

            <label style={labelStyle}>Número de Folds: {dossier.data.user_constraints.cv_strategy.folds}</label>
            <input 
              type="range" min="2" max="20" 
              value={dossier.data.user_constraints.cv_strategy.folds}
              onChange={(e) => handleUpdateCV("folds", parseInt(e.target.value))}
              style={{width: '100%', accentColor: '#648f8c'}}
            />
          </section>

          {/* CARD: FILTROS Y ENSAMBLADOS */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><LayoutGrid size={16}/> Selección de Features</h3>
            <label style={labelStyle}>Umbral (Threshold): {dossier.data.user_constraints.feature_selection_threshold}</label>
            <input 
              type="number" step="0.01"
              value={dossier.data.user_constraints.feature_selection_threshold}
              onChange={(e) => handleUpdateConstraint("feature_selection_threshold", parseFloat(e.target.value))}
              style={{...mappingInputStyle, width: '100%', textAlign: 'left', padding: '5px'}}
            />

            <div style={{...infoRow, marginTop: '15px'}}>
              <label style={{...labelStyle, marginTop: 0}}>Permitir Ensamblados:</label>
              <input 
                type="checkbox" 
                checked={dossier.data.user_constraints.allow_ensembles}
                onChange={(e) => handleUpdateConstraint("allow_ensembles", e.target.checked)}
                style={{accentColor: '#648f8c', transform: 'scale(1.2)'}}
              />
            </div>
          </section>

          {/* CARD: PRIORIDADES */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Brain size={16}/> Prioridad de Optimización</h3>
            <select 
              multiple
              value={dossier.data.user_constraints.optimization_priority}
              onChange={(e) => {
                const values = Array.from(e.target.selectedOptions, option => option.value);
                handleUpdateConstraint("optimization_priority", values);
              }}
              style={{...selectStyle, width: '100%', height: '80px'}}
            >
              <option value="Performance">Performance (Precisión)</option>
              <option value="Interpretability">Interpretability (Explicación)</option>
              <option value="Inference Speed">Inference Speed (Latencia)</option>
              <option value="Training Speed">Training Speed (Tiempo)</option>
            </select>
            <span style={{fontSize: '10px', color: '#666', marginTop: '5px', display: 'block'}}>
              * Ctrl + Click para seleccionar varios
            </span>
          </section>

          {/* --- SECCIÓN: ESTRATEGIA DE MODELADO --- */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Brain size={16}/> Selección de Modelos</h3>
            
            <label style={labelStyle}>Modo de Competición:</label>
            <select 
              value={dossier.data.user_constraints.model_selection.mode}
              onChange={(e) => handleUpdateConstraint("model_selection", {
                ...dossier.data.user_constraints.model_selection, mode: e.target.value
              })}
              style={{...selectStyle, width: '100%', marginTop: '5px'}}
            >
              <option value="AUTONOMOUS_COMPETITION">Competición Autónoma</option>
              <option value="SINGLE_BEST_MODEL">Mejor Modelo Único</option>
              <option value="ENSEMBLE_ONLY">Solo Ensamblados</option>
            </select>

            <label style={labelStyle}>Librerías Permitidas:</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px', marginTop: '8px' }}>
              {["scikit-learn", "xgboost", "lightgbm", "catboost"].map((lib) => {
                const libs = dossier.data.user_constraints.model_selection.libraries;
                const isSelected = libs.includes(lib);
                return (
                  <button
                    key={lib}
                    onClick={() => {
                      const newLibs = isSelected ? libs.filter((l: string) => l !== lib) : [...libs, lib];
                      handleUpdateConstraint("model_selection", { ...dossier.data.user_constraints.model_selection, libraries: newLibs });
                    }}
                    style={{
                      ...miniBtnStyle,
                      padding: '4px 8px',
                      fontSize: '10px',
                      backgroundColor: isSelected ? '#648f8c' : '#121212',
                      color: isSelected ? 'white' : '#648f8c'
                    }}
                  >
                    {lib}
                  </button>
                );
              })}
            </div>
          </section>

          {/* --- SECCIÓN: OPTIMIZACIÓN DE HIPERPARÁMETROS --- */}
          <section style={cardStyle}>
            <h3 style={cardTitle}><Activity size={16}/> Hyperparameter Tuning</h3>
            
            <label style={labelStyle}>Tipo de Búsqueda:</label>
            <select 
              value={dossier.data.user_constraints.tuning_strategy.search_type}
              onChange={(e) => handleUpdateConstraint("tuning_strategy", {
                ...dossier.data.user_constraints.tuning_strategy, search_type: e.target.value
              })}
              style={{...selectStyle, width: '100%', marginTop: '5px'}}
            >
              <option value="Bayesian_Optimization">Bayesian Optimization (Smart)</option>
              <option value="Randomized_Search">Randomized Search (Fast)</option>
              <option value="Grid_Search">Grid Search (Exhaustive)</option>
            </select>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '10px' }}>
              <div>
                <label style={labelStyle}>Máx Intentos:</label>
                <input 
                  type="number" 
                  value={dossier.data.user_constraints.tuning_strategy.max_trials}
                  onChange={(e) => handleUpdateConstraint("tuning_strategy", {
                    ...dossier.data.user_constraints.tuning_strategy, max_trials: parseInt(e.target.value)
                  })}
                  style={{...mappingInputStyle, width: '100%'}}
                />
              </div>
              <div>
                <label style={labelStyle}>Timeout (s):</label>
                <input 
                  type="number" 
                  value={dossier.data.user_constraints.tuning_strategy.timeout}
                  onChange={(e) => handleUpdateConstraint("tuning_strategy", {
                    ...dossier.data.user_constraints.tuning_strategy, timeout: parseInt(e.target.value)
                  })}
                  style={{...mappingInputStyle, width: '100%'}}
                />
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

// --- NUEVOS ESTILOS PARA EDICIÓN ---

const deployBtnStyle: React.CSSProperties = {
  backgroundColor: "#648f8c",
  color: "white",
  border: "none",
  padding: "10px 20px",
  borderRadius: "8px",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  gap: "8px",
  fontWeight: "bold",
  boxShadow: "0 4px 14px 0 rgba(100, 143, 140, 0.39)"
};

const orderItemEditable: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "8px 12px",
  backgroundColor: "#121212",
  borderRadius: "6px",
  fontSize: "13px",
  color: "#ccc",
  borderLeft: "3px solid #648f8c",
  marginBottom: "4px"
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
  padding: "2px"
};

// ... Mantén el resto de tus estilos (containerStyle, cardStyle, etc.)

// --- NUEVOS ESTILOS PARA LA MATRIZ ---
const matrixTableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
  marginTop: "10px",
  fontSize: "11px"
};

const matrixHeaderStyle: React.CSSProperties = {
  padding: "4px",
  textAlign: "center",
  color: "#648f8c",
  borderBottom: "1px solid #333"
};

const matrixRowLabelStyle: React.CSSProperties = {
  padding: "4px",
  color: "#aaa",
  borderRight: "1px solid #333",
  textAlign: "left"
};

const matrixCellStyle: React.CSSProperties = {
  padding: "4px",
  textAlign: "center",
  borderBottom: "1px solid #222"
};

// ... (El resto de tus estilos anteriores)

// --- ESTILOS (Tus constantes se mantienen iguales) ---
// ... (containerStyle, headerStyle, etc. que ya tienes)

// --- ESTILOS ---
const containerStyle: React.CSSProperties = {
  backgroundColor: "#121212", color: "white", minHeight: "100vh", padding: "20px", fontFamily: "sans-serif"
};

const headerStyle: React.CSSProperties = {
  display: "flex", justifyContent: "space-between", marginBottom: "20px"
};

const contentLayout: React.CSSProperties = {
  display: "grid", gridTemplateColumns: "300px 1fr 300px", gap: "20px"
};

const sidebarStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "20px" };

const mainPanelStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: "15px" };

const cardStyle: React.CSSProperties = {
  backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333"
};

const cardTitle: React.CSSProperties = { color: "#648f8c", fontSize: "14px", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" };

const featureCard: React.CSSProperties = {
  backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333", display: "flex", flexDirection: "column", gap: "10px"
};

const featureName: React.CSSProperties = { fontWeight: "bold", color: "#648f8c", fontSize: "16px" };

const textAreaStyle: React.CSSProperties = {
  backgroundColor: "#121212", color: "#ccc", border: "1px solid #333", borderRadius: "8px", padding: "10px", fontSize: "12px", resize: "none", height: "60px"
};

const saveBtnStyle: React.CSSProperties = {
  backgroundColor: "#648f8c", color: "white", border: "none", padding: "10px 20px", borderRadius: "8px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", fontWeight: "bold"
};

const backBtnStyle: React.CSSProperties = {
  background: "none", border: "none", color: "#648f8c", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px"
};

const badge: React.CSSProperties = { backgroundColor: "#648f8c33", color: "#648f8c", padding: "4px 10px", borderRadius: "12px", fontSize: "12px", width: "fit-content" };

const igGrid: React.CSSProperties = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "5px", fontSize: "11px", marginTop: "10px", borderTop: "1px solid #333", paddingTop: "10px" };

const igItem: React.CSSProperties = { display: "flex", justifyContent: "space-between" };

const selectStyle: React.CSSProperties = { backgroundColor: "#121212", color: "white", border: "1px solid #333", borderRadius: "4px", padding: "2px 5px" };

const gridFeatures: React.CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "15px" };

export default ViewDataPage;
// --- ESTILOS ADICIONALES ---

const errorStyle: React.CSSProperties = {
  color: "#ff6b6b",
  padding: "40px",
  textAlign: "center",
  backgroundColor: "#1e1e1e",
  borderRadius: "12px",
  margin: "20px",
  border: "1px solid #ff6b6b33"
};

const infoRow: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "10px",
  fontSize: "13px",
  color: "#aaa"
};

const orderList: React.CSSProperties = {
  marginTop: "12px",
  display: "flex",
  flexDirection: "column",
  gap: "8px"
};

const orderItem: React.CSSProperties = {
  padding: "8px 12px",
  backgroundColor: "#121212",
  borderRadius: "6px",
  fontSize: "13px",
  color: "#ccc",
  borderLeft: "3px solid #648f8c"
};

const sectionTitle: React.CSSProperties = {
  color: "#fff",
  fontSize: "1.5rem",
  marginBottom: "20px",
  display: "flex",
  alignItems: "center",
  gap: "12px",
  fontWeight: "600"
};

const featureHeader: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  borderBottom: "1px solid #333",
  paddingBottom: "10px",
  marginBottom: "5px"
};

const labelStyle: React.CSSProperties = {
  fontSize: "11px",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
  color: "#648f8c",
  fontWeight: "bold",
  marginTop: "10px"
};
const mappingRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  backgroundColor: "#121212",
  padding: "5px 10px",
  borderRadius: "6px",
  fontSize: "12px"
};

const mappingInputStyle: React.CSSProperties = {
  width: "40px",
  backgroundColor: "#1e1e1e",
  border: "1px solid #333",
  color: "#648f8c",
  borderRadius: "4px",
  textAlign: "center",
  fontSize: "12px",
  outline: "none"
};