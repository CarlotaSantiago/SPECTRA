import React from "react";
import { FileText, CheckCircle } from "lucide-react";

interface Artifact {
  name: string;
  size_bytes: number;
  kind: string;
}

interface ArtifactsListProps {
  artifacts: Artifact[];
}

export const ArtifactsList: React.FC<ArtifactsListProps> = ({ artifacts }) => {
  if (artifacts.length === 0) return null;

  return (
    <div style={styles.card}>
      <h3 style={styles.cardTitle}><FileText size={16}/> Artefactos Generados ({artifacts.length})</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {artifacts.map((art, index) => (
          <div key={index} style={styles.artifactRow}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={14} color="#648f8c" />
              <span style={{ fontSize: '12px', fontWeight: '500' }}>{art.name}</span>
            </div>
            <span style={{ fontSize: '10px', color: '#666' }}>
              {(art.size_bytes / 1024).toFixed(2)} KB | {art.kind}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  card: { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333", flex: '0 0 auto', maxHeight: '200px', overflowY: 'auto' },
  cardTitle: { color: "#648f8c", fontSize: "14px", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px", fontWeight: "bold" },
  artifactRow: { display: "flex", justifyContent: "space-between", alignItems: "center", backgroundColor: "#151515", padding: "6px 10px", borderRadius: "6px", border: "1px solid #252525" }
};