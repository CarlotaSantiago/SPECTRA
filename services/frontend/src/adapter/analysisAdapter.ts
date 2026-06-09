// src/adapters/configAdapter.ts
import { post, ollamaGet } from "./xhr";
import type { DossierPayload } from "../types"
import axios from "axios";

export const processState1 = (dossier: DossierPayload) => {
    return post("/process-state1", dossier);
}

export type LLMModelOption = { id: string; label: string };

export type LLMProviderEntry = {
  id: string;
  display_name: string;
  default_model: string;
  models: LLMModelOption[];
};

export type LLMProvidersResponse = {
  default_provider?: string;
  default_model?: string;
  providers: LLMProviderEntry[];
};

export const getLLMProviders = async (): Promise<LLMProvidersResponse> => {
  try {
    const response = await axios.get("http://localhost:8000/llm/providers");
    return response.data;
  } catch (error) {
    console.error("Error al obtener proveedores LLM", error);
    return { providers: [] };
  }
};

export const getModelsOllama = async (): Promise<string[]> => {
  try {
    const response = await axios.get("http://localhost:8000/models");

    if (response.data && response.data.status == "ok"){
      return response.data.models;
    }
    return ["llama3"];
  
  } catch (error) {
    console.error("Error al obtener el listado unificado de modelos", error);
    // Fallback de rescate en el cliente con los datos reales que viste en consola
    return [
      "llama3", 
      "ia.drorras.info/qwen2.5:14b-instruct-q4_K_M",
      "ia.drorras.info/qwen3:8b"
    ];
  }
};