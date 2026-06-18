import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Upload from './pages/UploadPage';
import DataConfig from './pages/DataConfigPage';
import ViewData from './pages/ViewDataPage';
import ViewScript from './pages/ViewScriptPage';
import ViewSesult from './pages/ViewResultsPage';

function App() {
  return (
    <Router>
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        backgroundColor: '#121212' // Evita destellos blancos al cargar
      }}>
        
        <header style={{ 
          padding: '10px', 
          borderBottom: '1px solid #536765', 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#536765', 
          textAlign: 'center',
          flexShrink: 0 
        }}>
          SPECTRA
        </header>

        <main style={{ 
          flexGrow: 1, 
          overflow: 'hidden', 
          display: 'flex', 
          flexDirection: 'column' 
        }}>
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path='/config-data' element={<DataConfig />} />
            <Route path='/view-data' element={<ViewData />} />
            <Route path='/edit-script' element={<ViewScript />} />
            <Route path='/results' element={<ViewSesult />} />
          </Routes>
        </main>

      </div>
    </Router>
  );
}

export default App;