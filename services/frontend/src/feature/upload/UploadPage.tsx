import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useUpload } from "./hooks/useUpload";
import { Dropzone } from "./components/Dropzone";
import { FileList } from "./components/FileList";
import { LoadingOverlay } from "./components/LoadingOverlay"; // Importamos el nuevo componente

const UploadPage = () => {
  const navigate = useNavigate();
  const [isUploading, setIsUploading] = useState(false);

  const { files, addFiles, removeFile, togglePreprocess, upload } =
    useUpload(async (data) => {
      if (data.status === "ok") {
        navigate("/data-config", { state: { data: data } });
      }
      setIsUploading(false);
    });

  const handleUpload = async () => {
    if (files.length === 0) return;
    setIsUploading(true);
    try {
      await upload();
    } catch (error) {
      setIsUploading(false);
      alert("Error al procesar la solicitud.");
    }
  };

  // Estilos de la página
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

  return (
    <div style={containerStyle}>
      {/* Componente extraído */}
      {isUploading && <LoadingOverlay />}

      <div style={{ width: "100%", maxWidth: "900px", textAlign: "center" }}>
        <h2 style={{ marginBottom: "20px", color: "#648f8c" }}>
          Selecciona Archivos para Procesar
        </h2>

        {files.length === 0 && <Dropzone onFiles={addFiles} />}

        <FileList
          files={files}
          remove={removeFile}
          toggle={togglePreprocess}
        />

        <button
          onClick={handleUpload}
          disabled={files.length === 0 || isUploading}
          style={btnStyle(files.length === 0 || isUploading)}
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