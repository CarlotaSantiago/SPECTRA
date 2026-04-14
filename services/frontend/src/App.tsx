import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Upload from './pages/Upload';
import PredictionPage from './pages/PredictionPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <header style={{ padding: '10px', borderBottom: '1px solid #536765', fontSize: '24px', fontWeight: 'bold', color: '#536765', textAlign: 'center' }}>
        Proyectito
      </header>

      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path='/prediction' element={<PredictionPage />} />
        <Route path='/results' element={<ResultsPage />} />
      </Routes>
    </Router>
  );
}

export default App;