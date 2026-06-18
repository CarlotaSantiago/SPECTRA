/**
 * @file UploadPage.tsx
 * @description Vista inicial del pipeline (Stage 0).
 * Permite al usuario seleccionar un archivo de dataset (CSV, Excel, Parquet) 
 * y enviarlo al backend para su almacenamiento y conteo de columnas.
 */

import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useUpload } from "../feature/hooks/useUpload";
import { Dropzone } from "../feature/components/Dropzone";
import { FileItem } from "../feature/components/FileItem";
import { LoadingOverlay } from "../feature/components/LoadingOverlay"; 
import { useDatasetStore } from "../store/useDatasetStore";

/**
 * Página principal que renderiza el área de Drag & Drop y gestiona la
 * redirección automática hacia la etapa de configuración de columnas una 
 * vez el backend valida la subida.
 */

export const UploadPage = () => {
  const navigate = useNavigate();
  const [isUploading, setIsUploading] = useState(false);

  const setData = useDatasetStore((s) => s.setData);

  const { file, addFile, removeFile, upload } = useUpload(async (data) => {
    if (data.status === "ok") {
      setData(data);
      navigate("/config-data");
    } else {
      console.error("La respuesta del servidor no es válida:", data);
    }
    setIsUploading(false);
  });

  const handleUpload = async () => {
    if (!file || file.length === 0) return;
    setIsUploading(true);
    try {
      await upload();
    } catch (error) {
      setIsUploading(false);
      alert("Error al procesar la solicitud.");
    }
  };

  const handleAddFile = (newFiles: File[]) => {
    if (file && file.length > 0) {
      alert("Solo puedes cargar un archivo a la vez.");
      return;
    }
    const allowedExtensions = ['.xlsx', '.xls', '.csv', '.parquet'];
    const fileExtension = newFiles[0].name.substring(newFiles[0].name.lastIndexOf('.')).toLowerCase();

    if (!allowedExtensions.includes(fileExtension)) {
      alert(`Formato de archivo no soportado. Por favor, sube un archivo: ${allowedExtensions.join(', ')}`);
      return; 
    }
    addFile([newFiles[0]]);
  };

  const containerStyle: React.CSSProperties = {
    width: "100%",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: "20px",
    backgroundColor: "#1a1a1a",
    color: "white"
  };

  const btnStyle = (disabled: boolean): React.CSSProperties => ({
    padding: "12px",
    width: "65%",
    borderRadius: "10px",
    border: "none",
    backgroundColor: "#648f8c",
    color: "white",
    fontWeight: "bold",
    cursor: disabled ? "not-allowed" : "pointer",
    marginTop: "30px",
    fontSize: "16px",
    opacity: disabled ? 0.6 : 1,
    transition: "background-color 0.2s",
  });

  const hasFile = file && file.length > 0;

  return (
    <div style={containerStyle}>
      {isUploading && <LoadingOverlay />}

      <div style={{ width: "100%", maxWidth: "900px", textAlign: "center" }}>
        <h2 style={{ marginBottom: "20px", color: "#648f8c" }}>
          Selecciona un Archivo para Procesar
        </h2>

        {!hasFile && <Dropzone onFiles={handleAddFile} />}

        {hasFile && (
          <FileItem
            item={file[0]}
            onRemove={() => removeFile(0)}
          />
        )}

        <button
          onClick={handleUpload}
          disabled={!hasFile || isUploading}
          style={btnStyle(!hasFile || isUploading)}
        >
          {isUploading ? "Cargando..." : "Lanzar Documentos"}
        </button>

        <footer style={{ marginTop: "20px", fontSize: "12px", color: "#888" }}>
          Result Key: Dossier Inicial (Features/Targets)
        </footer>
      </div>
    </div>
  );
};

export default UploadPage;