// src/adapters/xhr/index.ts
import axios from "axios";

const instance = axios.create({
  baseURL: "http://localhost:8000",
});

export const post = async <T = any>(url: string, data: any): Promise<T> => {
  const res = await instance.post(url, data);
  return res.data;
};