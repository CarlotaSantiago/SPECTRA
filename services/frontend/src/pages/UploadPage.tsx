import { useState } from 'react';

const UploadPage = () => {
  const [files, setFile] = useState<File[]>([]);

  const [preprocess, setPreprocess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(Array.from(e.target.files));
    }

  };

  const handleUpload = () => {
    if (files.length === 0) {
      alert("Por favor, selecciona uno o más archivos primero.");
      return;
    }
    const fromData = new FormData();
    files.forEach(file => fromData.append('files', file));
    fromData.append('preprocess', preprocess.toString());
    console.log("Enviando a backend:", { files: files.map(f => f.name), preprocess });
    // Aquí es donde conectarás con tu API de Python usando Axios
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Carga de Documentos</h2>
      <p>Selecciona los archivos para subir y preprocesar</p>
      
      <input type="file" multiple onChange={handleFileChange} />
      

      <label style={{ marginLeft: '10px' }}>
        <input type="checkbox" checked={preprocess} onChange={(e) => setPreprocess(e.target.checked)} /> Preprocesar antes de subir
      </label>

      {files.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <p>Archivos seleccionados:</p>
          <ul>
            {files.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}

      <br />
      <button 
        onClick={handleUpload}
        style={{ marginLeft: '10px', cursor: 'pointer' }}
      >
        Subir al Servidor
      </button>
    </div>
  );
};

export default UploadPage;