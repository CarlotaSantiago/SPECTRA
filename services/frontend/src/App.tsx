import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import UploadPage from './pages/UploadPage';

function App() {
  return (
    <Router>
      <object style={{ padding: '10px', borderBottom: '1px solid #ccc' }}>
        Proyecto Simple
      </object>

      <Routes>
        <Route path="/" element={<UploadPage />} />
      </Routes>
    </Router>
  );
}

export default App;