import { useState } from 'react';
import axios from 'axios';

const UploadPage = () => {
  const [files, setFile] = useState<File[]>([]);

  const [preprocess, setPreprocess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(Array.from(e.target.files));
    }

  };

  const handleUpload = async () => {
  
    console.log("1. Intentando enviar..."); // Esto debe salir en F12
  
  if (files.length === 0) {
    alert("Selecciona archivos");
    return;
  }

  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  formData.append('preprocess', String(preprocess));

  try {
    console.log("2. Llamando a la API...");
    // CAMBIO: Usa 127.0.0.1 en lugar de localhost por si acaso
    const response = await axios.post('http://127.0.0.1:8000/upload', formData);
    
    console.log("3. Respuesta recibida:", response.data);
  } catch (error) {
    console.error("4. ERROR DETECTADO:", error);
    alert("Error al conectar. Revisa la consola (F12)");
  }    
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