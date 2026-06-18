/**
 * @file useOllamaModels.ts
 * @description Hook complejo para orquestar la obtención y unificación de 
 * modelos LLM disponibles (tanto locales vía Ollama como remotos vía APIs externas).
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  getModelsOllama,
  getLLMProviders,
} from "../../adapter/analysisAdapter";

type ModelSelection = { model: string; provider?: string };

/**
 * Hook que provee el catálogo consolidado de modelos de IA.
 * 
 * @returns Array de nombres a mostrar (`models`), estado de carga (`loading`), 
 * y la función `resolveSelection` para mapear el nombre UI al ID real del backend.
 */
export const useOllamaModels = () => {
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const selectionByDisplay = useRef<Map<string, ModelSelection>>(new Map());

  /**
   * Mapea el texto seleccionado en el Dropdown a su identificador interno real
   * y proveedor necesario para el backend.
   */
  const resolveSelection = useCallback((display: string): ModelSelection => {
    return selectionByDisplay.current.get(display) ?? { model: display };
  }, []);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const [ollamaModels, providersData] = await Promise.all([
          getModelsOllama(),
          getLLMProviders(),
        ]);

        const selectionMap = new Map<string, ModelSelection>();
        const localModels: string[] = [];
        const drordasModels: string[] = [];
        const cloudDisplays: string[] = [];

        // 1. Procesamiento de modelos de Ollama (Locales / Drordas)
        for (const model of ollamaModels) {
          selectionMap.set(model, { model });
          if (model.includes("ia.drordas.info")) {
            drordasModels.push(model);
          } else {
            localModels.push(model);
          }
        }

        // 2. Procesamiento de modelos remotos de Cloud Providers (ej. OpenAI)
        for (const provider of providersData.providers ?? []) {
          if (provider.id === "ollama") continue;
          for (const model of provider.models ?? []) {
            const display = `[${provider.display_name}] ${model.label}`;
            cloudDisplays.push(display);
            selectionMap.set(display, {
              model: model.id,
              provider: provider.id,
            });
          }
        }

        selectionByDisplay.current = selectionMap;
        setModels([...localModels, ...drordasModels, ...cloudDisplays]);
      } catch (error) {
        console.error("Error al cargar modelos", error);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  return { models, loading, resolveSelection };
};
