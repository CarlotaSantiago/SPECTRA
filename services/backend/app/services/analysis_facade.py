"""
Módulo de fachada para la orquestación del análisis de datos y clasificación semántica.

Centraliza y coordina el flujo completo de procesamiento de un dataset: desde la carga segura,
la clasificación técnica y el cálculo de ganancia de información, hasta la generación de muestreos,
la consulta con un LLM (Ollama) para clasificación semántica y la estructuración del plan de orquestación.
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, Any

from app.schemas import ManifestSchema
from app.services.storage_service import StorageService
from app.services.analysis.classifier import classify_data, compute_information_gain
from app.services.utils.device import get_device
from app.services.llm.factory import call_ollama
from app.services.analysis.processor import limpiar_datos
from app.services.analysis.toon_builder import build_toon_payload, integrar_analisis_llm
from app.services.utils.sampling import stratified_sample_100
from app.services.orchestration.factory import build_chain_strategy
from app.services.orchestration.matrix import compute_target_dependency_matrix

logger = logging.getLogger(__name__)

class AnalysisFacade:
    """
    Facade para encapsular el complejo flujo de trabajo del análisis de datos
    y la orquestación, proporcionando una interfaz simplificada al router.
    """
    
    @staticmethod
    async def process_dataset(data: ManifestSchema) -> Dict[str, Any]:
        """
        Ejecuta el pipeline integral de análisis técnico y enriquecimiento por LLM.
        
        Coordina de manera asíncrona la limpieza de características, el cálculo de métricas de 
        ganancia de información, la inferencia de estructuras nominales/ordinales mediante prompts, 
        y la construcción final de la matriz de dependencia y el plan de orquestación del modelo.
        """
        device = get_device()
        logger.info(f"TRABAJANDO CON: {device}")

        df = StorageService.read_dataset(data.path)
        df = df.fillna("")
        if df.empty:
            raise ValueError("Dataset is empty")
        
        if not data.targets:
            raise ValueError("No targets provided")
        
        n_rows = data.n_rows

        # 1. Análisis de variables objetivo
        target_meta = {
            target: classify_data(df[target], n_rows)
            for target in data.targets
            if target in df.columns
        }
        
        columnas = list(data.targets)
        analysis_results = {}
        dossier = {"classified_evaluation": {}}
        columnas_limpias = {}
        
        # 2. Análisis de características y limpieza
        for col in data.features:
            if col not in df.columns:
                logger.warning(f"Column not found: {col}")
                continue

            series = df[col]
            col_data = classify_data(series, n_rows)

            update_data = {
                "user_mandatory": col in data.shielded,
                "unique_pool": series.dropna().astype(str).unique()[:20].tolist()
            }

            if col in data.shielded:
                update_data["llm_instruction"] = (
                    "This feature is statistically irrelevant, but the user requires its inclusion "
                    "for business reasons. Generate code that includes it in every stage of the pipeline."
                )

            col_data.update(update_data)

            if col_data["technical_level"] in [1, 2]:
                columnas.append(col)
                columnas_limpias[col] = df[col]
            else:
                columnas_limpias[col] = limpiar_datos(df[col])

            is_discrete = col_data["technical_level"] in [1, 2]

            col_data["information_gain"] = compute_information_gain(
                df, col, data.targets, target_meta, is_discrete, device=device
            )
            analysis_results[col] = col_data
            if col_data["technical_level"] in [1, 3, 4]:
                dossier["classified_evaluation"][col] = col_data

        # 3. Guardar dataset limpio
        df_limpio = pd.DataFrame(columnas_limpias).assign(**{t: df[t] for t in data.targets if t in df.columns})
        save_path = "uploads/datos_limpios.xlsx"
        StorageService.save_dataset(df_limpio, save_path)
        
        # 4. Generar payload para LLM
        sample_df = stratified_sample_100(df[columnas], data.targets)
        sample_df_clean = sample_df.astype(object).fillna("")
        metadata = {"n_rows": n_rows, "targets": data.targets}

        logger.info(f"Modelo: {data.model}")
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

        user_prompt = build_toon_payload(metadata, analysis_results, sample_df_clean, data.features, target_meta)
        
        with open("toon_dossier.txt", "w", encoding="utf-8") as f:
            f.write(user_prompt)
            
        # 5. Ejecutar LLM
        semantic_analysis = await call_ollama(data.model, system_prompt, user_prompt, state=1)
        
        # 6. Integración y Orquestación
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
        
        json_tecnico["orchestration_plan"] = orquestation.to_dict()
        
        with open("toon_dossier.json", "w", encoding="utf-8") as f:
            json.dump(json_tecnico, f, indent=4, ensure_ascii=False)
            
        return {
            "status": "ok",
            "path": save_path,
            "extension": os.path.splitext(save_path)[1],
            "data": json_tecnico
        }