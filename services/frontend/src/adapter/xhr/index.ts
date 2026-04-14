// src/adapters/xhr/index.ts
import axios from "axios";

const instance = axios.create({
  baseURL: "http://localhost:8000",
});

export const post = (url: string, data: any) => instance.post(url, data);