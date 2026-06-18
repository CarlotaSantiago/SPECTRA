/**
 * @file xhr/index.ts
 * @description Configuración centralizada de los clientes HTTP (Axios) para la aplicación.
 * Define las instancias base para interactuar con la API principal de SPECTRA y con el daemon de Ollama.
 */

import axios from "axios";

/** URL base de la API principal de SPECTRA */
export const API_BASE_URL = "http://localhost:8000";

/** URL base de la API local de Ollama para consultar modelos disponibles */
const OLLAMA_BASE_URL = "http://localhost:11434/api";

/** 
 * Cliente principal apuntando al backend de SPECTRA.
 * Las cabeceras de autenticación o interceptores globales se deben configurar en esta instancia.
 */
const instance = axios.create({ baseURL: API_BASE_URL });

/** 
 * Cliente secundario y específico para interactuar directamente con la API local de Ollama.
 */
const ollamaInstance = axios.create({ baseURL: OLLAMA_BASE_URL });

/**
 * Función genérica de abstracción para realizar peticiones GET a la API principal.
 * 
 * @param url - La ruta del endpoint relativo a la API_BASE_URL (ej. "/models").
 * @param params - Diccionario opcional de query parameters a adjuntar en la URL.
 * @returns La propiedad `data` de la respuesta, tipada genéricamente.
 */
export const get = async <T = any>(
  url: string,
  params?: Record<string, any>
): Promise<T> => {
  const res = await instance.get(url, { params });
  return res.data;
};

/**
 * Función genérica de abstracción para realizar peticiones POST a la API principal.
 * 
 * @param url - La ruta del endpoint relativo a la API_BASE_URL.
 * @param data - El body de la petición, habitualmente un objeto JSON o un FormData.
 * @returns La propiedad `data` de la respuesta, tipada genéricamente.
 */
export const post = async <T = any>(url: string, data: any): Promise<T> => {
  const res = await instance.post(url, data);
  return res.data;
};

/**
 * Realiza una petición GET específicamente dirigida al servicio local de Ollama.
 * 
 * @param url - Ruta relativa al OLLAMA_BASE_URL.
 * @returns La propiedad `data` de la respuesta.
 */
export const ollamaGet = async <T = any>(url: string): Promise<T> => {
  const res = await ollamaInstance.get(url);
  return res.data;
};