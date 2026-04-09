import { useLocation, useNavigate } from 'react-router-dom';

const ResultsPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const results = location.state?.results;

    if (!results) {
        return (
            <div style={{ backgroundColor: '#000', color: '#fff', height: '100vh', padding: '20px' }}>
                <p>No hay datos. Realiza una predicción primero.</p>
                <button onClick={() => navigate(-1)} style={btnBackStyle}>Volver</button>
            </div>
        );
    }

    // --- LÓGICA PARA ORGANIZAR LAS COLUMNAS ---
    // Extraemos todos los modelos activos de todos los bloques (mio, hombro, prioridad)
    const columnasPrediccion: { bloque: string; modelo: string }[] = [];
    
    Object.keys(results).forEach(bloque => {
        Object.keys(results[bloque]).forEach(modelo => {
            columnasPrediccion.push({ bloque, modelo });
        });
    });

    // Asumimos que todos los modelos predijeron sobre el mismo número de filas
    const primeraClaveBloque = Object.keys(results)[0];
    const primeraClaveModelo = Object.keys(results[primeraClaveBloque])[0];
    const totalFilas = results[primeraClaveBloque][primeraClaveModelo].predicciones.length;

    return (
        <div style={{ padding: '30px', backgroundColor: '#000', minHeight: '100vh', color: '#fff', fontFamily: 'Arial' }}>
            <h2 style={{ color: '#648f8c', marginBottom: '20px' }}>📊 Matriz Comparativa de Resultados IA</h2>

            <div style={{ overflowX: 'auto', backgroundColor: '#1a1a1a', borderRadius: '12px', padding: '10px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', color: '#eee' }}>
                    <thead>
                        <tr style={{ borderBottom: '2px solid #648f8c' }}>
                            <th style={thStyle}>Paciente #</th>
                            {/* Generamos una cabecera por cada predicción solicitada */}
                            {columnasPrediccion.map((col, i) => (
                                <th key={i} style={thStyle}>
                                    <span style={{ fontSize: '0.7em', color: '#888', display: 'block' }}>{col.bloque.toUpperCase()}</span>
                                    {col.modelo.replace('_', ' ')}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {[...Array(totalFilas)].map((_, rowIndex) => (
                            <tr key={rowIndex} style={rowStyle}>
                                <td style={{ ...tdStyle, fontWeight: 'bold', color: '#888' }}>{rowIndex + 1}</td>
                                
                                {columnasPrediccion.map((col, colIndex) => {
                                    const prediccion = results[col.bloque][col.modelo].predicciones[rowIndex];
                                    return (
                                        <td key={colIndex} style={tdStyle}>
                                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                                <span style={getLabelStyle(prediccion.label)}>
                                                    {prediccion.label}
                                                </span>
                                                <span style={{ fontSize: '0.7em', color: '#648f8c', marginTop: '4px' }}>
                                                    {prediccion.confianza}
                                                </span>
                                            </div>
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div style={{ marginTop: '30px' }}>
                <button onClick={() => navigate(-1)} style={btnBackStyle}>Nueva Configuración</button>
            </div>
        </div>
    );
};

// --- ESTILOS ---
const thStyle: React.CSSProperties = { padding: '15px', textAlign: 'center', borderBottom: '1px solid #333' };
const tdStyle: React.CSSProperties = { padding: '15px', textAlign: 'center', borderBottom: '1px solid #2a2a2a' };
const rowStyle: React.CSSProperties = { transition: '0.2s' };

const btnBackStyle = { padding: '12px 25px', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' };

const getLabelStyle = (label: string): React.CSSProperties => {
    let color = '#fff';
    let bgColor = '#444';

    if (label === 'A' || label === 'MIO' || label === 'HOMBRO') {
        bgColor = '#8b2e2e'; // Rojo oscuro para prioridad alta o positivo
    } else if (label === 'B') {
        bgColor = '#8b7a2e'; // Amarillo/Naranja
    } else if (label === 'C' || label === 'NO MIO' || label === 'NO HOMBRO') {
        bgColor = '#2e8b57'; // Verde
    }

    return {
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '0.9em',
        fontWeight: 'bold',
        backgroundColor: bgColor,
        color: color,
        display: 'inline-block'
    };
};

export default ResultsPage;