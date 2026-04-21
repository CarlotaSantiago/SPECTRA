// src/adapters/configAdapter.ts
import { post, ollamaGet } from "./xhr";
import type { DossierPayload } from "../types"

export const processState1 = (dossier: DossierPayload) => {
    return post("/process-state1", dossier);
}

export const getModelsOllama = async (): Promise<string[]> => {
  try {
    const data = await ollamaGet("/tags");
    // Ollama devuelve un objeto con una lista de modelos
    return data.models.map((m: any) => m.name);
  } catch (error) {
    console.warn("Ollama local no detectado, cargando modelos recomendados.");
    // Estos son los modelos que sugirió tu profesor
    return ["qwen2.5-coder", "deepseek-coder", "llama3"];
  }
};