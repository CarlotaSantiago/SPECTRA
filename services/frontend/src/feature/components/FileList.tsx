import { FileItem } from "./FileItem";
import type { FileWithSettings } from "../../types";

export const FileList = ({
  files,
  remove,
  toggle,
}: {
  files: FileWithSettings[];
  remove: (i: number) => void;
  toggle: (i: number) => void;
}) => {
  if (files.length === 0) return null;

  return (
    <div style={{ marginTop: "30px" }}>
      <h3 style={{ marginBottom: "15px", fontSize: "18px" }}>
        Archivo qque se desea subir:
      </h3>

      {files.map((f, i) => (
        <FileItem
          key={i}
          item={f}
          onRemove={() => remove(i)}
          onToggle={() => toggle(i)}
        />
      ))}
    </div>
  );
};