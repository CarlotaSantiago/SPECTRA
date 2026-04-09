import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

interface ProcessedFile {
    filename: string;
    preprocessed: boolean;
}

// Definimos los modelos disponibles
const MODELOS_BINARIOS = [
    { key: 'random_forest', name: 'Random Forest' },
    { key: 'svm', name: 'SVM' },
    { key: 'naive_bayes', name: 'Naive Bayes' },
    { key: 'mlp', name: 'MLP' },
];

const MODELOS_PRIORIDAD = [
    { key: 'decision_tree', name: 'Decision Tree' },
    { key: 'gradient_boosting', name: 'Gradient Boosting' },
    { key: 'random_forest_multi', name: 'Random Forest Multi' },
];

const PredictionPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const processedFiles: ProcessedFile[] = location.state?.data || [];

    // 1. Estados de activación global
    const [useMio, setUseMio] = useState(false);
    const [useHombro, setUseHombro] = useState(false);
    const [usePrioridad, setUsePrioridad] = useState(false);

    // 2. Estados de selección de documentos
    const [mioDocs, setMioDocs] = useState<string[]>([]);
    const [hombroDocs, setHombroDocs] = useState<string[]>([]);
    const [prioridadDocs, setPrioridadDocs] = useState<string[]>([]);

    // 3. NUEVO: Estados de selección de modelos de IA
    const [mioSelectedModels, setMioSelectedModels] = useState<string[]>([]);
    const [hombroSelectedModels, setHombroSelectedModels] = useState<string[]>([]);
    const [prioridadSelectedModels, setPrioridadSelectedModels] = useState<string[]>([]);

    const toggleItem = (id: string, list: string[], setList: (val: string[]) => void) => {
        if (list.includes(id)) {
            setList(list.filter(item => item !== id));
        } else {
            setList([...list, id]);
        }
    };

    const handleRunPrediction = async () => {
        const payload = {
            mio: {
                active: useMio,
                models: mioSelectedModels,
                files: mioDocs
            },
            hombro: {
                active: useHombro,
                models: hombroSelectedModels,
                files: hombroDocs
            },
            prioridad: {
                active: usePrioridad,
                models: prioridadSelectedModels,
                files: prioridadDocs
            }
        };

        try {
            const response = await axios.post('http://localhost:8000/predict', payload);
            if (response.data.status === "success") {
            // Navegamos a la ruta '/results' y pasamos los datos en el estado de la navegación
            navigate('/results', { state: { results: response.data.data } });
            }
        } catch (error) {
            console.error("Error:", error);
        }
    };

    const handleRunTraining = async () => {
        const payload = {
            mio: {
                active: useMio,
                models: mioSelectedModels,
                files: mioDocs
            },
            hombro: {
                active: useHombro,
                models: hombroSelectedModels,
                files: hombroDocs
            },
            prioridad: {
                active: usePrioridad,
                models: prioridadSelectedModels,
                files: prioridadDocs
            }
        };

        try {
            const response = await axios.post('http://localhost:8000/train', payload);
            console.log("Respuesta:", response.data);
        } catch (error) {
            console.error("Error:", error);
        }
    };

    // Sub-componente para renderizar los selectores de modelos
    const ModelSelector = ({ models, selectedList, toggleFn, active }: any) => (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '15px', opacity: active ? 1 : 0.5 }}>
            {models.map((m: any) => (
                <button
                    key={m.key}
                    onClick={() => active && toggleFn(m.key)}
                    style={{
                        padding: '4px 10px',
                        borderRadius: '16px',
                        border: '1px solid #648f8c',
                        fontSize: '0.75em',
                        cursor: active ? 'pointer' : 'default',
                        backgroundColor: selectedList.includes(m.key) ? '#648f8c' : 'transparent',
                        color: selectedList.includes(m.key) ? 'white' : '#648f8c',
                        transition: '0.2s'
                    }}
                >
                    {m.name}
                </button>
            ))}
        </div>
    );

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial', backgroundColor: '#000', minHeight: '100vh', color: '#fff' }}>
            <h2 style={{ color: '#648f8c' }}>Configuración de Análisis</h2>
            <p>Configura los motores de IA y los archivos a procesar:</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
                
                {/* BLOQUE 1: MÍO / NO MÍO */}
                <section style={{ ...sectionStyle, borderTop: useMio ? '5px solid #648f8c' : '5px solid #444' }}>
                    <div style={headerStyle}>
                        <input type="checkbox" checked={useMio} onChange={(e) => setUseMio(e.target.checked)} style={checkboxLarge} />
                        <h3 style={{ margin: 0, color: useMio ? '#648f8c' : '#999' }}>Mío / No Mío</h3>
                    </div>
                    
                    <div style={{ pointerEvents: useMio ? 'auto' : 'none' }}>
                        <p style={subTitleStyle}>Escoger Modelos de IA:</p>
                        <ModelSelector 
                            models={MODELOS_BINARIOS} 
                            selectedList={mioSelectedModels} 
                            toggleFn={(id: string) => toggleItem(id, mioSelectedModels, setMioSelectedModels)}
                            active={useMio}
                        />

                        <p style={subTitleStyle}>Seleccionar Archivos:</p>
                        {processedFiles.map((file, i) => (
                            <label key={i} style={itemStyle(mioDocs.includes(file.filename))}>
                                <input type="checkbox" checked={mioDocs.includes(file.filename)} onChange={() => toggleItem(file.filename, mioDocs, setMioDocs)} />
                                {file.filename}
                            </label>
                        ))}
                    </div>
                </section>

                {/* BLOQUE 2: HOMBRO / NO HOMBRO */}
                <section style={{ ...sectionStyle, borderTop: useHombro ? '5px solid #648f8c' : '5px solid #444' }}>
                    <div style={headerStyle}>
                        <input type="checkbox" checked={useHombro} onChange={(e) => setUseHombro(e.target.checked)} style={checkboxLarge} />
                        <h3 style={{ margin: 0, color: useHombro ? '#648f8c' : '#999' }}>Hombro / NH</h3>
                    </div>
                    <div style={{ pointerEvents: useHombro ? 'auto' : 'none' }}>
                        <p style={subTitleStyle}>Escoger Modelos de IA:</p>
                        <ModelSelector 
                            models={MODELOS_BINARIOS} 
                            selectedList={hombroSelectedModels} 
                            toggleFn={(id: string) => toggleItem(id, hombroSelectedModels, setHombroSelectedModels)}
                            active={useHombro}
                        />
                        <p style={subTitleStyle}>Seleccionar Archivos:</p>
                        {processedFiles.map((file, i) => (
                            <label key={i} style={itemStyle(hombroDocs.includes(file.filename))}>
                                <input type="checkbox" checked={hombroDocs.includes(file.filename)} onChange={() => toggleItem(file.filename, hombroDocs, setHombroDocs)} />
                                {file.filename}
                            </label>
                        ))}
                    </div>
                </section>

                {/* BLOQUE 3: PRIORIDAD */}
                <section style={{ ...sectionStyle, borderTop: usePrioridad ? '5px solid #648f8c' : '5px solid #444' }}>
                    <div style={headerStyle}>
                        <input type="checkbox" checked={usePrioridad} onChange={(e) => setUsePrioridad(e.target.checked)} style={checkboxLarge} />
                        <h3 style={{ margin: 0, color: usePrioridad ? '#648f8c' : '#999' }}>Prioridad</h3>
                    </div>
                    <div style={{ pointerEvents: usePrioridad ? 'auto' : 'none' }}>
                        <p style={subTitleStyle}>Escoger Modelos Terciarios</p>
                        <ModelSelector 
                            models={MODELOS_PRIORIDAD} 
                            selectedList={prioridadSelectedModels} 
                            toggleFn={(id: string) => toggleItem(id, prioridadSelectedModels, setPrioridadSelectedModels)}
                            active={usePrioridad}
                        />
                        <p style={subTitleStyle}>Escoger modelos Binarios</p>
                        <ModelSelector 
                            models={MODELOS_BINARIOS} 
                            selectedList={prioridadSelectedModels} 
                            toggleFn={(id: string) => toggleItem(id, prioridadSelectedModels, setPrioridadSelectedModels)}
                            active={usePrioridad}
                        />
                        <p style={subTitleStyle}>Seleccionar Archivos:</p>
                        {processedFiles.map((file, i) => (
                            <label key={i} style={itemStyle(prioridadDocs.includes(file.filename))}>
                                <input type="checkbox" checked={prioridadDocs.includes(file.filename)} onChange={() => toggleItem(file.filename, prioridadDocs, setPrioridadDocs)} />
                                {file.filename}
                            </label>
                        ))}
                    </div>
                </section>
            </div>

            <div style={{ marginTop: '30px', textAlign: 'center' }}>
                <button onClick={() => navigate('/')} style={btnBackStyle}>Volver</button>
                <button onClick={handleRunPrediction} style={btnRunStyle}>Lanzar Predicciones</button>
                <button onClick={handleRunTraining} style={btnRunStyle}>Lanzar Entrenamiento</button>
            
            </div>
        </div>
    );
};

// Estilos actualizados para fondo negro del componente
const sectionStyle: React.CSSProperties = {
    backgroundColor: '#1a1a1a',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.5)',
    transition: '0.3s'
};

const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '15px',
    paddingBottom: '10px',
    borderBottom: '1px solid #333'
};

const itemStyle = (selected: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 12px',
    margin: '4px 0',
    borderRadius: '6px',
    cursor: 'pointer',
    backgroundColor: selected ? '#648f8c' : '#2a2a2a',
    color: selected ? 'white' : '#ccc',
    fontSize: '0.85em',
    transition: '0.2s'
});

const subTitleStyle = { fontSize: '0.75em', fontWeight: 'bold', color: '#888', marginBottom: '8px', textTransform: 'uppercase' as 'uppercase' };
const checkboxLarge = { width: '18px', height: '18px', cursor: 'pointer' };
const btnRunStyle = { padding: '12px 25px', backgroundColor: '#648f8c', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' as 'bold' };
const btnBackStyle = { padding: '12px 20px', marginRight: '15px', backgroundColor: '#333', color: '#eee', border: 'none', borderRadius: '8px', cursor: 'pointer' };

export default PredictionPage;