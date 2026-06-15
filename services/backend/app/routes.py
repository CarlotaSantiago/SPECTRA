from importlib.resources import path
import io
import json
import logging
import os
import re
import requests

import numpy as np
import pandas as pd
import torch
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from pandas.api.types import is_float_dtype, is_numeric_dtype, is_object_dtype, is_string_dtype
from pydantic import BaseModel
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder
from typing import Any, Dict, List
from app.services.classify import classify_data, compute_information_gain, encode_series
from app.services.device_detection import get_device
from app.services.routeOllama import call_ollama
from app.services.processor import limpiar_datos
from app.services.build_toon import build_toon_payload, integrar_analisis_llm
from app.services.strarified_sampling import stratified_sample_100
from app.services.orchestation import build_chain_strategy, compute_target_dependency_matrix
from app.services.training_service_proxy import proxy_llm_providers, proxy_process_state2

logger = logging.getLogger(__name__)


# 1. Usamos el APIRouter()
router = APIRouter()

@router.get("/models")
def get_available_models():
    """
    Lista los modelos locales y consume de forma exacta la API 
    del profesor detectada en el test.
    """
    local_models = []
    profesor_models = []

    # 1. Intentamos recuperar tus modelos locales (Ollama local API)
    try:
        response_local = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response_local.status_code == 200:
            local_models = [m["name"] for m in response_local.json().get("models", [])]
    except Exception:
        # Fallback local por si tu Ollama local está apagado en este momento
        local_models = ["llama3", "qwen2.5-coder:7b"]

    # 2. Consumimos el endpoint del profesor (Estructura OpenAI validada)
    try:
        url_profesor = "http://ia.drordas.info:11434/v1/models"
        response_profe = requests.get(url_profesor, timeout=3)

        if response_profe.status_code == 200:
            data_profe = response_profe.json()
            # Iteramos sobre la lista 'data' exacta que viste en el CMD
            for m in data_profe.get("data", []):
                model_id = m.get("id")
                if model_id:
                    # Le anteponemos el dominio para identificarlo en el frontend
                    profesor_models.append(f"ia.drordas.info/{model_id}")
    except Exception as e:
        print(f"[BACKEND] No se pudo conectar a la URL externa: {e}")
        # Modelos de contingencia basados en tu captura si falla la red
        profesor_models = [
        ]

    # Devolvemos la combinación de ambos orígenes
    return {"status": "ok", "models": local_models + profesor_models}


@router.get("/llm/providers")
def get_llm_providers():
    body, status = proxy_llm_providers()
    return JSONResponse(content=body, status_code=status)


@router.post("/upload") # 2. Cambiamos 'app.post' por 'router.post'
async def handle_upload(
    file: UploadFile = File(...),
    preprocess: bool = Form(...)
):
    """
    Handle file upload and preprocessing.
    
    Args:
        file: one file for preprocessing.
        indices_to_preprocess: JSON string containing indices of files to preprocess.
    
    Returns:
        Status and results of the upload and preprocessing.
    """
    try: 
        content = await file.read()

        if file.filename.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(io.BytesIO(content))
        else:
            # Añadimos soporte para CSV por si acaso
            data = pd.read_csv(io.BytesIO(content))

        if preprocess:
            columnas_a_limpiar = ['datosclini', 'sospechadiag']
            for col in columnas_a_limpiar:
                if col in data.columns:
                    data[f'{col}_limpio'] = limpiar_datos(data[col])

        n_rows = len(data)
        final_columns = data.columns.tolist()

        if preprocess:
            save_path = os.path.join("uploads", f"procesado_{file.filename}")
            data.to_excel(save_path, index=False)
        else:
            save_path = os.path.join("uploads", file.filename)
            data.to_excel(save_path, index=False)

        # Limpiar valores problemáticos para JSON
        data.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Convertir NaN a None (compatible con JSON)
        preview = data.head(10).replace({np.nan: None}).to_dict(orient='records')

        return {
            "status": "ok", 
            "n_rows": n_rows,
            "columnas": final_columns,
            "preview": preview,
            "path": save_path
        }
    except Exception as e:
        logger.error(f"Error en upload: {e}")

        return {
            "status": "error",
            "message": str(e)
        }
    
@router.get("/get-page")
def get_page(path: str, page: int = 1, size: int =150, filters: str = "{}"):
    try:
        if path.endswith(('.xlsx', '.xls')):
            data = pd.read_excel(path)
        else:
            data = pd.read_csv(path)
        
        try:
            filter_dict = json.loads(filters)
            for col, value in filter_dict.items(): # <--- AQUÍ ESTABA EL ERROR
                if value and col in data.columns:
                    data = data[data[col].astype(str).str.contains(str(value), case=False, na=False)]
        except Exception as f_err:
            print(f"Error parseando filtros: {f_err}")
            # Si los filtros fallan, seguimos adelante con la data original
        
        n_rows = len(data)

        start = (page -1) * size
        end = start + size

        data_page = data.iloc[start:end].replace({np.nan: None, np.inf: None, -np.inf: None})

        return {
            "status": "ok",
            "items": data_page.to_dict(orient='records'),
            "n_rows": n_rows,
            "page": page,
            "size": size
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


class Dossier(BaseModel):
    """Model representing a dossier with total count, 
    path, features, targets, and mandatory fields."""
    n_rows: int
    path: str
    features: List[str]
    targets: List[str]
    mandatory: List[str]
    model: str

@router.post("/process-state1")
def process_state_1(data: Dossier):
    try:
        # 1. Carga de datos (Soporte para Excel y CSV con manejo de encoding)
        
        device = get_device()
        print(f"TRABAJANDO CON: {device}")

        df = pd.read_excel(data.path)
        df = df.fillna("")
        if df.empty:
            raise ValueError("Dataset is empty")
        
        if not data.targets:
            raise ValueError("No targets provided")
        
        n_rows = data.n_rows

        target_meta = {
            target: classify_data(df[target], n_rows)
            for target in data.targets
            if target in df.columns
        }
        columnas = list(data.targets)
        analysis_results = {}
        dossier = {
            "classified_evaluation": {}
        }
        columnas_limpias = {}
        for col in data.features:
            if col not in df.columns:
                logger.warning(f"Column not found: {col}")
                continue


            series = df[col]

            col_data = classify_data(series, n_rows)

            col_data.update({
                "user_mandatory": col in data.mandatory,
                "unique_pool": series.dropna().astype(str).unique()[:20].tolist()
            })

            if col_data["technical_level"] in [1, 2]:
                columnas.append(col)
                columnas_limpias[col] = df[col]
            else:
                columnas_limpias[col] = limpiar_datos(df[col])


            is_discrete = col_data["technical_level"] in [1, 2]

            col_data["information_gain"] = compute_information_gain(
                df,
                col,
                data.targets,
                target_meta,
                is_discrete,
                device=device
            )
            analysis_results[col] = col_data
            if col_data["technical_level"] in [1, 3, 4]:
                dossier["classified_evaluation"][col] = col_data

        save_path = "uploads/datos_limpios.xlsx"
        new_data = pd.DataFrame(columnas_limpias)
        for target in data.targets:
            if target in df.columns:
                new_data[target] = df[target]
        new_data.to_excel(save_path, index=False)
        sample_df = stratified_sample_100(df[columnas], data.targets)
        sample_df_clean = sample_df.astype(object).fillna("")
        metadata ={
            "n_rows": n_rows, 
            "targets": data.targets
        }

        print("Modelo: " + data.model)
        system_prompt = """/nothink
            You are a Data Science Assistant specialized in semantic feature classification.
            Your ONLY task: classify each feature in CATEGORICAL_SUBCLASS_EVALUATION and each target in TARGETS_SUBCLASS_EVALUATION as NOMINAL or ORDINAL.

            OUTPUT FORMAT — reproduce this structure exactly, one entry per feature:
            # SEMANTIC_CLASSIFICATION_RESULTS
            feature_name:
            subclass: NOMINAL
            mapping: null
            reasoning: one sentence.

            feature_name:
            subclass: ORDINAL
            mapping: {value1: 0, value2: 1, value3: 2}
            reasoning: one sentence.

            # TARGETS_SUBCLASS_EVALUATION
            target_name:
            subclass: NOMINAL
            mapping: null
            reasoning: one sentence.

            target_name:
            subclass: ORDINAL
            mapping: {value1: 0, value2: 1, value3: 2}
            reasoning: one sentence.

            CLASSIFICATION RULES:
            1. ORDINAL: values have a natural, unambiguous order or hierarchy (e.g. Junior < Senior, Baja < Alta).
            2. NOMINAL: values are distinct categories with no inherent order (e.g. departments, service codes).
            3. Use representative_sample to observe how values relate to targets before deciding.
            4. If uncertain between ORDINAL and NOMINAL, default to NOMINAL.
            5. For ORDINAL, mapping must include ALL values from unique_pool, starting at 0.
            6. For NOMINAL, mapping must be null.

            STRICT OUTPUT RULES:
            - Output ONLY the # SEMANTIC_CLASSIFICATION_RESULTS and # TARGETS_SUBCLASS_EVALUATION blocks.
            - No explanations outside the reasoning field.
            - No recommendations, no observations, no markdown headers beyond the block.
            - No bullet points, no numbered lists.
            - One entry per feature and target, in the same order as CATEGORICAL_SUBCLASS_EVALUATION and TARGETS_SUBCLASS_EVALUATION.
            """

        toon = build_toon_payload(metadata, analysis_results, sample_df_clean, data.features, target_meta)
        user_prompt = toon
        with open("toon_dossier.txt", "w", encoding="utf-8") as f:
            f.write(user_prompt)
        semantic_analysis = call_ollama(data.model, system_prompt, user_prompt, state=1)
        with open("toon_dossier.json", "r", encoding="utf-8") as f:
            contenido = json.load(f)
        json_tecnico = integrar_analisis_llm(contenido, semantic_analysis)
        json_tecnico.update(dossier)
        df_for_matrix = df.sample(n=min(10000, len(df)), random_state=42) if len(df) > 0 else df
        matriz = compute_target_dependency_matrix(df_for_matrix, data.targets, json_tecnico["targets_evaluation"])
        threshold_config = getattr(data, 'threshold_cfg', 'auto')
        orquestation = build_chain_strategy(df, matriz, json_tecnico["targets_evaluation"], threshold_config, json_tecnico)
        matrix_dict = matriz.to_dict(orient='index')
        json_tecnico["target_dependency_matrix"] = matrix_dict
        max_dep = float(matriz.where(matriz < 1.0).max().max())
        json_tecnico["orchestration_plan"] = {
            "strategy": orquestation['strategy'],
            "order": orquestation['order'] if orquestation.get('order') is not None else [],
            "gating": orquestation.get('gating'),
            "dependents": orquestation.get('dependents', []),
            "max_dependency": max_dep
        }
        with open("toon_dossier.json", "w", encoding="utf-8") as f:
            json.dump(json_tecnico, f, indent=4, ensure_ascii=False)
        return {
            "status": "ok",
            "path": save_path,
            "extension": os.path.splitext(save_path)[1],
            "data": json_tecnico
        }

    except Exception as e:
        logger.error(f"process_state_1 failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }



@router.post("/process-state2")
def process_state_2(data: Dict[str, Any]):
    try:
        body, status_code = proxy_process_state2(data)
        return JSONResponse(content=body, status_code=status_code)
    except Exception as e:
        logger.error("process_state_2 proxy failed: %s", e)
        return {"status": "error", "message": str(e)}