// feature/components/ScriptEditor.tsx
import React from "react";
import { Code } from "lucide-react";

interface ScriptEditorProps {
  code: string;
  onChange: (newCode: string) => void;
}

export const ScriptEditor: React.FC<ScriptEditorProps> = ({ code, onChange }) => (
  <div style={styles.codePanel}>
    <h3 style={styles.cardTitle}><Code size={16}/> Script de Entrenamiento Python</h3>
    <textarea
      value={code}
      onChange={(e) => onChange(e.target.value)}
      style={styles.codeEditor}
      spellCheck={false}
    />
    <div style={styles.editorDisclaimer}>
      * Las modificaciones en este script se enviarán directamente al backend para su ejecución.
    </div>
  </div>
);

const styles: Record<string, React.CSSProperties> = {
  codePanel: { backgroundColor: "#1e1e1e", padding: "15px", borderRadius: "12px", border: "1px solid #333", display: "flex", flexDirection: "column", flex: 1 },
  codeEditor: { flex: 1, backgroundColor: "#0b0b0b", color: "#a9dc76", border: "1px solid #222", borderRadius: "6px", padding: "12px", fontFamily: "Courier New, monospace", fontSize: "12px", lineHeight: "1.5", resize: "none", outline: "none", minHeight: "350px" },
  cardTitle: { color: "#648f8c", fontSize: "14px", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px", fontWeight: "bold" },
  editorDisclaimer: { fontSize: '11px', color: '#666', marginTop: '5px' }
};