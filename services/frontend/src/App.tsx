import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import PredictionPage from './pages/PredictionPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <object style={{ padding: '10px', borderBottom: '1px solid #ccc' }}>
        Proyecto Simple
      </object>

      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path='/prediction' element={<PredictionPage />} />
        <Route path='/results' element={<ResultsPage />} />
      </Routes>
    </Router>
  );
}

export default App;