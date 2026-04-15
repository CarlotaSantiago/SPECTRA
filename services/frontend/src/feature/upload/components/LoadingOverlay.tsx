import { Loader2 } from "lucide-react";

interface LoadingOverlayProps {
  message?: string;
}

export const LoadingOverlay = ({ message = "Procesando documentos..." }: LoadingOverlayProps) => {
  const overlayStyle: React.CSSProperties = {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100vw",
    height: "100vh",
    backgroundColor: "rgba(26, 26, 26, 0.85)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 9999,
    backdropFilter: "blur(4px)",
    color: "#648f8c",
  };

  return (
    <div style={overlayStyle}>
      <Loader2 size={50} style={{ animation: "spin 1s linear infinite" }} />
      <h3 style={{ marginTop: "15px", fontWeight: "bold" }}>{message}</h3>
      <p style={{ color: "#888", fontSize: "14px" }}>Esto puede tardar unos segundos</p>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};