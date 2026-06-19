/**
 * @file analysisAdapter.ts
 * @description Capa adaptadora para interactuar con los endpoints relacionados al 
 * análisis semántico y la obtención de modelos LLM (State 1).
 */

import { post, get } from "./xhr";
import type { ManifestPayload } from "../types";

/**
 * Envía el manifiesto inicial (Dataset subido + configuración de columnas) al backend 
 * para iniciar el proceso de evaluación de metadatos y análisis semántico.
 * 
 * @param manifest - Objeto con la metadata de filas, columnas ocultas y el LLM elegido.
 * @returns Promesa que resuelve al Dossier completo con la evaluación generada.
 */
export const processState1 = (manifest: ManifestPayload) => {
  console.log("Process State 1:", manifest);
  return post("/process-state1", manifest);
};

// ── Tipos de modelos LLM ──────────────────────────────────────────────────────

/** Representación de un modelo LLM específico soportado por un proveedor */
export type LLMModelOption = { id: string; label: string };

/** Proveedor LLM remoto (ej. OpenAI, Groq) junto con sus modelos disponibles */
export type LLMProviderEntry = {
  id: string;
  display_name: string;
  default_model: string;
  models: LLMModelOption[];
};

/** Respuesta del endpoint de proveedores que agrupa toda la configuración remota */
export type LLMProvidersResponse = {
  default_provider?: string;
  default_model?: string;
  providers: LLMProviderEntry[];
};

// ── Consultas a endpoints del backend ────────────────────────────────────────

/** 
 * Consulta al backend para obtener los proveedores remotos configurados y sus modelos,
 * en base a las API Keys inyectadas en el backend.
 * 
 * @returns Una promesa con la lista de proveedores. Devuelve array vacío si falla.
 */
export const getLLMProviders = async (): Promise<LLMProvidersResponse> => {
  try {
    return await get<LLMProvidersResponse>("/llm/providers");
  } catch (error) {
    console.error("Error al obtener proveedores LLM:", error);
    return { providers: [] };
  }
};

/** 
 * Obtiene la lista unificada de todos los modelos disponibles, consultando al 
 * daemon local de Ollama a través del backend.
 * Implementa un fallback robusto con modelos de seguridad en caso de caída del daemon.
 * 
 * @returns Un array simple con los identificadores en string de cada modelo.
 */
export const getModelsOllama = async (): Promise<string[]> => {
  try {
    const data = await get<{ status: string; models: string[] }>("/models");
    if (data?.status === "ok") return data.models;
    return ["llama3"];
  } catch (error) {
    console.error("Error al obtener el listado unificado de modelos:", error);
    return [
      "llama3",
      "ia.drorras.info/qwen2.5:14b-instruct-q4_K_M",
      "ia.drorras.info/qwen3:8b",
    ];
  }
};