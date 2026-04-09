import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const ResultsPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const results = location.state?.results;

    console.log("Datos recibidos:", results);

    if (!results) {
        return <div style={errorContainerStyle}>No hay datos. <button onClick={() => navigate(-1)}>Volver</button></div>;
    }

    const columnasIA: { bloque: string; modelo: string }[] = [];
    Object.keys(results).forEach(bloque => {
        Object.keys(results[bloque]).forEach(modelo => {
            columnasIA.push({ bloque, modelo });
        });
    });

    if (columnasIA.length === 0) return <div style={errorContainerStyle}>Estructura de datos no reconocida.</div>;

    // 2. Obtenemos las predicciones y los datos originales (si existen)
    const primerModelo = results[columnasIA[0].bloque][columnasIA[0].modelo];
    const prediccionesLista = primerModelo.predicciones || [];
    const datosExcel = primerModelo.datos_originales || [];

    return (
        <div style={pageContainerStyle}>
            <header style={headerStyle}>
                <h1 style={{ margin: 0, color: '#648f8c' }}>RESULTADOS ({prediccionesLista.length} registros)</h1>
                <button onClick={() => navigate(-1)} style={btnBackStyle}>Volver</button>
            </header>

            <div style={tableWrapperStyle}>
                <table style={tableStyle}>
                    <thead>
                        <tr>
                            <th style={thStyle}>#</th>
                            <th style={thStyle}>Edad</th>
                            <th style={{ ...thStyle, width: '300px' }}>Datos Clínicos</th>
                            <th style={thStyle}>Sospecha</th>
                            {columnasIA.map((col, i) => (
                                <th key={i} style={iaThStyle}>
                                    <span style={{fontSize: '10px', opacity: 0.6}}>{col.bloque}</span><br/>
                                    {col.modelo.toUpperCase()}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {prediccionesLista.map((_: any, rowIndex: number) => {
                            const filaExcel = datosExcel[rowIndex] || {};
                            return (
                                <tr key={rowIndex} style={trStyle}>
                                    <td style={{...tdStyle, color: '#555'}}>{rowIndex + 1}</td>
                                    <td style={tdStyle}>{filaExcel.edad || '—'}</td>
                                    <td style={{ ...tdStyle, textAlign: 'left', fontSize: '0.8em', color: '#bbb' }}>
                                        {filaExcel.datosclini || 'No disponible'}
                                    </td>
                                    <td style={{ ...tdStyle, textAlign: 'left' }}>
                                        {filaExcel.sospechadiag || '—'}
                                    </td>

                                    {columnasIA.map((col, colIndex) => {
                                        const bloqueData = results[col.bloque];
                                        const modeloData = bloqueData ? bloqueData[col.modelo] : null;
                                        const p = modeloData?.predicciones?.[rowIndex];

                                        return (
                                            <td key={colIndex} style={tdStyle}>
                                                {p ? (
                                                    <>
                                                        <div style={getLabelStyle(p.label)}>
                                                            {p.label}
                                                        </div>
                                                        <div style={confidenceStyle}>
                                                            {/* Convertimos el float 0.85 a "85%" */}
                                                            {typeof p.confianza === 'number' 
                                                                ? (p.confianza * 100).toFixed(1) + '%' 
                                                                : p.confianza || 'N/A'}
                                                        </div>
                                                    </>
                                                ) : '—'}
                                            </td>
                                        );
                                    })}
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// --- ESTILOS ---
const pageContainerStyle: React.CSSProperties = { padding: '20px', backgroundColor: '#000', minHeight: '100vh', color: '#fff', fontFamily: 'Arial' };
const headerStyle: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', marginBottom: '20px' };
const tableWrapperStyle: React.CSSProperties = { overflow: 'auto', maxHeight: '80vh', border: '1px solid #333' };
const tableStyle: React.CSSProperties = { width: '100%', borderCollapse: 'collapse' };
const thStyle: React.CSSProperties = { padding: '12px', backgroundColor: '#111', color: '#888', borderBottom: '2px solid #333', fontSize: '12px' };
const iaThStyle: React.CSSProperties = { ...thStyle, color: '#648f8c', backgroundColor: '#0a1514' };
const tdStyle: React.CSSProperties = { padding: '10px', borderBottom: '1px solid #222', textAlign: 'center' };
const trStyle = { borderBottom: '1px solid #222' };
const confidenceStyle = { fontSize: '10px', color: '#648f8c', marginTop: '4px' };
const btnBackStyle = { padding: '8px 16px', backgroundColor: '#333', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' };
const errorContainerStyle: React.CSSProperties = { color: 'white', textAlign: 'center', marginTop: '50px' };

const getLabelStyle = (label: string): React.CSSProperties => {
    let bg = '#333';
    if (['A', 'MIO', 'HOMBRO'].includes(label)) bg = '#600';
    if (['B'].includes(label)) bg = '#660';
    if (['C', 'NO MIO', 'NO HOMBRO'].includes(label)) bg = '#060';
    return { padding: '4px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold', backgroundColor: bg };
};

export default ResultsPage;