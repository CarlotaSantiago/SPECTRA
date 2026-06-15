import { FileText, X } from "lucide-react";
import type { FileWithSettings } from "../../types";

export const FileItem = ({
  item,
  onRemove,
}: {
  item: FileWithSettings;
  onRemove: () => void;
}) => {
  const fileCardStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 18px",
    borderRadius: "10px",
    marginBottom: "10px",
  };

  return (
    <div style={fileCardStyle}>
      {/* Info archivo */}
      <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
        <FileText color="#648f8c" size={24} />

        <div>
          <p style={{ margin: 0, fontWeight: 500 }}>
            {item.file.name}
          </p>
          <p style={{ margin: 0, fontSize: "11px", color: "#64748b" }}>
            {(item.file.size / 1024).toFixed(1)} KB
          </p>
        </div>
      </div>

        <X
          size={18}
          color="#ef4444"
          style={{ cursor: "pointer" }}
          onClick={onRemove}
        />
      </div>
  );
};