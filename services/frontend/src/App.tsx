import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Upload from './pages/UploadPage';
import DataConfig from './pages/DataConfigPage';
import Prediction from './pages/PredictionPage';
import Results from './pages/ResultsPage';
import ViewData from './pages/ViewDataPage';

function App() {
  return (
    <Router>
      <header style={{ padding: '10px', borderBottom: '1px solid #536765', fontSize: '24px', fontWeight: 'bold', color: '#536765', textAlign: 'center' }}>
        Proyectito
      </header>

      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path='/data-config' element={<DataConfig />} />
        <Route path='/prediction' element={<Prediction />} />
        <Route path='/results' element={<Results />} />
        <Route path='/view-results' element={<ViewData />} />
      </Routes>
    </Router>
  );
}

export default App;