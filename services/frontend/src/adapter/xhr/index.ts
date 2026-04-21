// src/adapters/xhr/index.ts
import axios from "axios";

const instance = axios.create({
  baseURL: "http://localhost:8000",
});

const ollamaInstance = axios.create({
  baseURL: "http://localhost:11434/api"
})

export const post = async <T = any>(url: string, data: any): Promise<T> => {
  const res = await instance.post(url, data);
  return res.data;
};

// GET específico para Ollama
export const ollamaGet = async <T = any>(url: string): Promise<T> => {
  const res = await ollamaInstance.get(url);
  return res.data;
};