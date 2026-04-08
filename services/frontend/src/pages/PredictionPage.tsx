import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';

interface ProcessedFile {
    filename: string;
    preprocessed: boolean;
}

const modelos = [
    {key: 'random_forest', name: 'Random Forest'},
    {key: 'svm', name: 'Support Vector Machine'},
    {key: 'naive_bayes', name: 'Naive Bayes'},
    {key: 'mlp', name: 'Multilayer Perceptron'},
]

const PredictionPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const processedFiles: ProcessedFile[] = location.state?.data || [];

    // 1. Estados para activar/desactivar el tipo de predicción globalmente
    const [useMio, setUseMio] = useState(false);
    const [useHombro, setUseHombro] = useState(false);
    const [usePrioridad, setUsePrioridad] = useState(false);

    // 2. Estados para los documentos seleccionados en cada categoría
    const [mioDocs, setMioDocs] = useState<string[]>([]);
    const [hombroDocs, setHombroDocs] = useState<string[]>([]);
    const [prioridadDocs, setPrioridadDocs] = useState<string[]>([]);

    const toggleDoc = (filename: string, list: string[], setList: (val: string[]) => void) => {
        if (list.includes(filename)) {
            setList(list.filter(item => item !== filename));
        } else {
            setList([...list, filename]);
        }
    };

    const handleRunPrediction = async () => {
        const payload = {
            mio_no_mio: useMio ? mioDocs : null,
            hombro_no_hombro: useHombro ? hombroDocs : null,
            prioridad: usePrioridad ? prioridadDocs : null
        };

        try {
            const response = await axios.post('http://127.0.0.1:8000/predict', payload, {
                headers: { 
                    'Content-Type': 'application/json' 
                }
            });
            console.log("Respuesta de predicción:", response.data);
        } catch (error) {
            console.error("Error al enviar predicciones:", error);
            alert("Error al enviar predicciones. Revisa la consola (F12)");
        }
     };

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial', backgroundColor: '#000000', minHeight: '100vh' }}>
            <h2>Configuración de Análisis</h2>
            <p>Activa los modelos que deseas ejecutar y selecciona los archivos para cada uno:</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
                
                {/* BLOQUE 1: MÍO / NO MÍO */}
                <section style={{ ...sectionStyle, borderTop: useMio ? '5px solid #648f8c' : '5px solid #ccc' }}>
                    <div style={headerStyle}>
                        <input 
                            type="checkbox" 
                            checked={useMio} 
                            onChange={(e) => setUseMio(e.target.checked)} 
                            style={checkboxLarge}
                        />
                        <h3 style={{ margin: 0, color: useMio ? '#648f8c' : '#999' }}>Mío / No Mío</h3>
                    </div>
                    
                    <div style={{ opacity: useMio ? 1 : 0.4, pointerEvents: useMio ? 'auto' : 'none' }}>
                        <p style={subTitleStyle}>Selecciona archivos para este análisis:</p>
                        {processedFiles.map((file, i) => (
                            <label key={i} style={itemStyle(mioDocs.includes(file.filename))}>
                                <input 
                                    type="checkbox" 
                                    checked={mioDocs.includes(file.filename)} 
                                    onChange={() => toggleDoc(file.filename, mioDocs, setMioDocs)}
                                />
                                {file.filename}
                            </label>
                        ))}
                    </div>
                </section>

                {/* BLOQUE 2: HOMBRO / NO HOMBRO */}
                <section style={{ ...sectionStyle, borderTop: useHombro ? '5px solid #648f8c' : '5px solid #ccc' }}>
                    <div style={headerStyle}>
                        <input 
                            type="checkbox" 
                            checked={useHombro} 
                            onChange={(e) => setUseHombro(e.target.checked)} 
                            style={checkboxLarge}
                        />
                        <h3 style={{ margin: 0, color: useHombro ? '#648f8c' : '#999' }}>Hombro / NH</h3>
                    </div>

                    <div style={{ opacity: useHombro ? 1 : 0.4, pointerEvents: useHombro ? 'auto' : 'none' }}>
                        <p style={subTitleStyle}>Selecciona archivos para este análisis:</p>
                        {processedFiles.map((file, i) => (
                            <label key={i} style={itemStyle(hombroDocs.includes(file.filename))}>
                                <input 
                                    type="checkbox" 
                                    checked={hombroDocs.includes(file.filename)} 
                                    onChange={() => toggleDoc(file.filename, hombroDocs, setHombroDocs)}
                                />
                                {file.filename}
                            </label>
                        ))}
                    </div>
                </section>

                {/* BLOQUE 3: PRIORIDAD */}
                <section style={{ ...sectionStyle, borderTop: usePrioridad ? '5px solid #648f8c' : '5px solid #ccc' }}>
                    <div style={headerStyle}>
                        <input 
                            type="checkbox" 
                            checked={usePrioridad} 
                            onChange={(e) => setUsePrioridad(e.target.checked)} 
                            style={checkboxLarge}
                        />
                        <h3 style={{ margin: 0, color: usePrioridad ? '#648f8c' : '#999'}}>Prioridad</h3>
                    </div>

                    <div style={{ opacity: usePrioridad ? 1 : 0.4, pointerEvents: usePrioridad ? 'auto' : 'none' }}>
                        <p style={subTitleStyle}>Selecciona archivos para este análisis:</p>
                        {processedFiles.map((file, i) => (
                            <label key={i} style={itemStyle(prioridadDocs.includes(file.filename))}>
                                <input 
                                    type="checkbox" 
                                    checked={prioridadDocs.includes(file.filename)} 
                                    onChange={() => toggleDoc(file.filename, prioridadDocs, setPrioridadDocs)}
                                />
                                {file.filename}
                            </label>
                        ))}
                    </div>
                </section>

            </div>

            <div style={{ marginTop: '30px', textAlign: 'center' }}>
                <button onClick={() => navigate('/')} style={btnBackStyle}>Volver</button>
                <button onClick={handleRunPrediction} style={btnRunStyle}>Lanzar Análisis Seleccionados</button>
            </div>
        </div>
    );
};

// --- Estilos ---

const sectionStyle: React.CSSProperties = {
    backgroundColor: '#fff',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    transition: '0.3s'
};

const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '15px',
    paddingBottom: '10px',
    borderBottom: '1px solid #eee'
};

const itemStyle = (selected: boolean): React.CSSProperties => ({
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 12px',
    margin: '4px 0',
    borderRadius: '4px',
    cursor: 'pointer',
    backgroundColor: selected ? '#648f8c' : '#f8f9fa',
    color: selected ? 'white' : '#333',
    fontSize: '0.9em'
});

const subTitleStyle = { fontSize: '0.8em', fontWeight: 'bold', color: '#666', marginBottom: '8px' };
const checkboxLarge = { width: '20px', height: '20px', cursor: 'pointer' };

const btnRunStyle = {
    padding: '12px 25px',
    backgroundColor: '#648f8c',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 'bold' as 'bold'
};

const btnBackStyle = {
    padding: '12px 20px',
    marginRight: '15px',
    backgroundColor: '#ccc',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
};

export default PredictionPage;