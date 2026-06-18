/**
 * @file App.tsx
 * @description Componente raíz de la aplicación SPECTRA. 
 * Configura el enrutador principal (React Router) definiendo el pipeline 
 * lineal de las cinco etapas principales de la herramienta.
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Upload from './pages/UploadPage';
import DataConfig from './pages/DataConfigPage';
import ViewData from './pages/ViewDataPage';
import ViewScript from './pages/ViewScriptPage';
import ViewResults from './pages/ViewResultsPage';

/**
 * Componente principal que define el layout global (Header + Main) 
 * y las rutas de la aplicación de extremo a extremo.
 */
function App() {
  return (
    <Router>
      <div style={appStyle}>
        <header style={headerStyle}>
          SPECTRA
        </header>
        <main style={mainStyle}>
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/config-data" element={<DataConfig />} />
            <Route path="/view-data" element={<ViewData />} />
            <Route path="/edit-script" element={<ViewScript />} />
            <Route path="/results" element={<ViewResults />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

const appStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: '#121212',
  minHeight: '100vh',
};

const headerStyle: React.CSSProperties = {
  padding: '10px',
  borderBottom: '1px solid #536765',
  fontSize: '24px',
  fontWeight: 'bold',
  color: '#536765',
  textAlign: 'center',
  flexShrink: 0,
};

const mainStyle: React.CSSProperties = {
  flexGrow: 1,
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
};

export default App;