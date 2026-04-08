import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';


interface FileWithSettings {
  file: File;
  preprocess: boolean;
}

const UploadPage = () => {
  const navigate = useNavigate();
  const [files, setFile] = useState<FileWithSettings[]>([]);

  const [preprocess, setPreprocess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files).map(file => ({
        file,
        preprocess
      }));
      setFile(selectedFiles);
    }

  };

  const togglePreprocessForFile = (index: number) => {
    setFile(prevFiles => 
      prevFiles.map((item, idx) =>   
        idx === index ? {...item, preprocess: !item.preprocess} : item
      )
    );
  };

  const handleUpload = async () => {
  
    console.log("1. Intentando enviar..."); // Esto debe salir en F12
  
  if (files.length === 0) {
    alert("Selecciona archivos");
    return;
  }

  const formData = new FormData();
  files.forEach((item, index) => {
      formData.append('files', item.file);
      formData.append(`preprocess_${index}`, String(item.preprocess));
    });

    const indicesToProcess = files
      .map((item, index) => (item.preprocess ? index : null))
      .filter((index) => index !== null);
    
    formData.append('indices_to_preprocess', JSON.stringify(indicesToProcess));
  try {
    console.log("2. Llamando a la API...");
    // CAMBIO: Usa 127.0.0.1 en lugar de localhost por si acaso
    const response = await axios.post('http://127.0.0.1:8000/upload', formData);
    
    console.log("3. Respuesta recibida:", response.data);
    if (response.data.status === "ok") {
      console.log("Archivos subidos y procesados correctamente");
      navigate('/prediction', { state: { data: response.data.results } });
    }
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

      {files.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <p><strong>Archivos seleccionados:</strong></p>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {files.map((item, index) => (
              <li key={index} style={{ marginBottom: '8px', display: 'flex', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  id={`file-${index}`}
                  checked={item.preprocess}
                  onChange={() => togglePreprocessForFile(index)}
                  style={{ marginRight: '10px', cursor: 'pointer' }}
                />
                <label htmlFor={`file-${index}`} style={{ cursor: 'pointer' }}>
                  {item.file.name} 
                  {item.preprocess && (
                    <span style={{ color: '#007bff', fontSize: '0.85em', marginLeft: '10px' }}>
                      (Preprocesar activado)
                    </span>
                  )}
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}

      <br />
      <button 
        onClick={handleUpload}
        disabled={files.length === 0}
        style={{ marginLeft: '10px', cursor: 'pointer' }}
      >
        Subir al Servidor
      </button>
    </div>
  );
};

export default UploadPage;