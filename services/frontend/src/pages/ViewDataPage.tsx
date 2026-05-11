import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { ArrowLeft, Save, Brain, LayoutGrid, Activity, ChevronUp, ChevronDown } from "lucide-react";
import { ModelPicker } from "../feature/components/ModelPicker";
import { useOllamaModels } from "../feature/hooks/useOllamaModels";

const ViewDataPage = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { models: ollamaModels, loading: loadingModels } = useOllamaModels();
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [selectedModel, setSelectedModel] = useState(""); // <-- 2. Estado del modelo
    
  const [dossier, setDossier] = useState<any>(state?.toonData || null);

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

    const payload = {
      dossier: dossier.data, // Los datos editados (incluyendo mappings y orden)
      config: {
        model: selectedModel,
        timestamp: new Date().toISOString(),
      }
    };

    try {
      const response = await fetch("http://localhost:8000/api/stage2/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const result = await response.json();
        alert("Configuración enviada con éxito. Iniciando entrenamiento...");
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
              style={{...selectStyle, width: '100%', marginBottom: '10px'}}
            >
              <option value="ClassifierChain">ClassifierChain</option>
              <option value="RegressorChain">RegressorChain</option>
              <option value="MultiOutput">MultiOutput</option>
              <option value="HybridChain">HybridChain</option>
            </select>

            <div style={orderList}>
              {dossier?.data?.orchestration_plan?.order?.map((target: string, i: number) => (
                <div key={target} style={orderItemEditable}>
                  <span>{i + 1}. {target}</span>
                  <div style={{display: 'flex', gap: '4px'}}>
                    <button 
                      onClick={() => moveOrderItem(i, 'up')} 
                      disabled={i === 0}
                      style={miniBtnStyle}
                    ><ChevronUp size={14}/></button>
                    <button 
                      onClick={() => moveOrderItem(i, 'down')} 
                      disabled={i === dossier.data.orchestration_plan.order.length - 1}
                      style={miniBtnStyle}
                    ><ChevronDown size={14}/></button>
                  </div>
                </div>
              ))}
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
          <h2 style={sectionTitle}><Brain size={20}/> Análisis de Variables Objetivo (Editable)</h2>
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
                  </div>
                  </div>
                </div>
                
              );
            })}
          </div>
          {/* SECCIÓN 1: VARIABLES CATEGÓRICAS (EDITABLES) */}
          <h2 style={sectionTitle}><Brain size={20}/> Análisis Semántico (Editable)</h2>
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
              <h2 style={{...sectionTitle, marginTop: '40px'}}><Activity size={20}/> Análisis Técnico (Solo Lectura)</h2>
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
  display: "grid", gridTemplateColumns: "300px 1fr", gap: "20px"
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