/**
 * @file dataAdapter.ts
 * @description Capa adaptadora para la gestión del flujo final de la aplicación: 
 * la generación física del script de Machine Learning a partir del Dossier (State 2).
 */

import { post } from "./xhr";
import type { GeneratePayload } from "../types";

/**
 * Envía el dossier definitivo y revisado por el usuario al backend para delegarle
 * al modelo LLM la escritura, validación y empaquetado del script final en Python.
 * Corresponde funcionalmente al endpoint `/process-state2`.
 * 
 * @param payload - Objeto que integra el dossier base y el modelo generador destino.
 * @returns Una promesa que resuelve al objeto que contiene el código fuente puro del script.
 */
export const deployDossier = async (payload: GeneratePayload) => {
  console.log("Process State 2",payload)
  return post("/process-state2", payload);
};

/**
 * Envía el script definitivo y modificado por el usuario al backend para ejecutarlo
 * y crear los modelos de las variables indicadas.
 * Corresponde funcionalmente al endpoint `/edit-script`.
 * 
 * @param payload - Objeto que integra el script base .
 * @returns Un objeto formato JSON donde indica las métricas finales de los modelos.
 */
export const editScript = async (payload: GeneratePayload) => {
  console.log("Entrenar modelos", payload)
  return post("/send-script", payload);
};