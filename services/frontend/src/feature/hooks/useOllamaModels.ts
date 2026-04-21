import { useState, useEffect } from 'react';
import { getModelsOllama } from "../../adapter/analysisAdapter"; 

export const useOllamaModels = () => {
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
    console.log("Lo esta intentando")
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const data = await getModelsOllama();
        setModels(data);
        console.log(data)
      } catch (error) {
        console.error("Error al cargar modelos de Ollama", error);
      } finally {
        setLoading(false);
      }
    };

    fetchModels();
  }, []);

  return { models, loading };
};