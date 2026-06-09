import { useState, useEffect, useCallback, useRef } from "react";
import {
  getModelsOllama,
  getLLMProviders,
} from "../../adapter/analysisAdapter";

type ModelSelection = { model: string; provider?: string };

export const useOllamaModels = () => {
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const selectionByDisplay = useRef<Map<string, ModelSelection>>(new Map());

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

        for (const model of ollamaModels) {
          selectionMap.set(model, { model });
          if (model.includes("ia.drordas.info")) {
            drordasModels.push(model);
          } else {
            localModels.push(model);
          }
        }

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
