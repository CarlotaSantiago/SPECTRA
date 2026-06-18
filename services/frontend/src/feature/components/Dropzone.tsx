import { useState } from "react";
import { Upload } from "lucide-react";

/**
 * Componente interactivo para subir archivos mediante "arrastrar y soltar" (Drag & Drop)
 * o mediante selección clásica del sistema de archivos.
 * 
 * @param props.onFiles - Callback ejecutado con el array de archivos (`File[]`) soltados o seleccionados.
 */
export const Dropzone = ({
  onFiles,
}: {
  onFiles: (files: File[]) => void;
}) => {
  const [isDragging, setIsDragging] = useState(false);

  const dropZoneStyle: React.CSSProperties = {
    border: `2px dashed ${isDragging ? "#648f8c" : "#444"}`,
    borderRadius: "15px",
    width: "50%",
    marginTop: "30px",
    margin: "0 auto",
    padding: "40px",
    textAlign: "center",
    cursor: "pointer",
    backgroundColor: isDragging
      ? "rgba(76, 201, 240, 0.1)"
      : "transparent",
    transition: "all 0.3s ease",
  };

  return (
    <div
      style={dropZoneStyle}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);

        const droppedFiles = Array.from(e.dataTransfer.files);
        onFiles(droppedFiles);
      }}
      onClick={() => document.getElementById("fileInput")?.click()}
    >
      <Upload size={48} color="#648f8c" style={{ marginBottom: "15px" }} />

      <p style={{ fontSize: "18px" }}>
        Arrastra tu archivo o haz clic aquí
      </p>

      <p style={{ fontSize: "12px", color: "#64748b" }}>
        CSV, Excel o Parquet admitidos
      </p>

      <input
        id="fileInput"
        type="file"
        multiple
        hidden
        onChange={(e) => {
          if (e.target.files) {
            onFiles(Array.from(e.target.files));
          }
        }}
      />
    </div>
  );
};