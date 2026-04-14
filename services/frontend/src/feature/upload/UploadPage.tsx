// src/features/upload/UploadPage.tsx
import { useNavigate } from "react-router-dom";
import { useUpload } from "./hooks/useupload";
import { Dropzone } from "./components/Dropzone";
import { FileList } from "./components/FileList";

const UploadPage = () => {
  const navigate = useNavigate();

  const { files, addFiles, removeFile, togglePreprocess, upload } =
    useUpload((data) => {
      if (data.status === "ok") {
        navigate("/prediction", { state: { data: data.results } });
      }
    });

  const containerStyle: React.CSSProperties = {
    width: "100%",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    paddingTop: "20px",
  };

  const contentStyle: React.CSSProperties = {
    width: "100%",
    maxWidth: "900px",
    textAlign: "center",
  };

  const btnStyle: React.CSSProperties = {
    padding: "12px",
    width: "65%",
    borderRadius: "10px",
    border: "none",
    backgroundColor: "#648f8c",
    color: "white",
    fontWeight: "bold",
    cursor: files.length > 0 ? "pointer" : "not-allowed",
    marginTop: "30px",
    fontSize: "16px",
    transition: "all 0.2s ease",
    opacity: files.length === 0 ? 0.6 : 1,
  };

  return (
    <div style={containerStyle}>
      <div style={contentStyle}>
        <h2 style={{ marginBottom: "20px" }}>
          Selecciona Archivos para Procesar
        </h2>

        {/* Dropzone */}
        {files.length === 0 && <Dropzone onFiles={addFiles} />}

        {/* Lista */}
        <FileList
          files={files}
          remove={removeFile}
          toggle={togglePreprocess}
        />

        {/* Botón */}
        <button
          onClick={upload}
          disabled={files.length === 0}
          style={btnStyle}
          onMouseOver={(e) =>
            (e.currentTarget.style.backgroundColor = "#557a77")
          }
          onMouseOut={(e) =>
            (e.currentTarget.style.backgroundColor = "#648f8c")
          }
        >
          Lanzar Documentos
        </button>

        <footer
          style={{
            marginTop: "20px",
            fontSize: "12px",
            color: "#444",
          }}
        >
          Result Key: Dossier Inicial (Features/Targets)
        </footer>
      </div>
    </div>
  );
};

export default UploadPage;