import re
import json

def build_toon_s2(metadata, type_correlation, max_dependency, dependency, target_meta, data):
    toon_str = "#LOCATION DATAFRAME\n"
    toon_str += f"path: {data['path']}\n"
    toon_str += f"extension_file: {data['extension']}\n\n"
    toon_str += "# DATASET_CONTEXT\n"
    toon_str += f"rows: {metadata['global_metadata']['total_rows']}\t| features: {metadata['global_metadata']['features']}\n"
    toon_str += f"target_correlation:   '{{type: {type_correlation}, dependency: {dependency}, p_value: {max_dependency} }}'\n\n"

    toon_str += "# USER_INTERFACE_CONSTRAINTS\n"
    toon_str += f"cv_strategy: '{{'strategy': {metadata['user_constraints']['cv_strategy']['type']}, 'folds': 1}}'\n"
    toon_str += f"feature_selection_threshold: {metadata['user_constraints']['feature_selection_threshold']}\n"
    toon_str += f"allow_ensembles: {metadata['user_constraints']['allow_ensembles']}\n"
    toon_str += f"optimization_priority: {metadata['user_constraints']['optimization_priority']}\n\n"

    toon_str += "# TARGET_STRATEGY_DOSSIER\n"
    toon_str += "targets:\n\t"
    for target, info in target_meta.items():
        toon_str += f"- name: {target}:\n\t"
        toon_str += f"- type: {info['subclass']}\n\t"
        toon_str += f"- dependency: {info['dependency']}\n\t"
        toon_str += f"- priority_metrics: {info['priority_metrics']}\n\n\t"

    
    toon_str += "# MODEL_SELECTION_GUIDELINES\n"
    toon_str += f"mode: {metadata['user_constraints']['model_selection']['mode']}\n"
    toon_str += f"libraries: {metadata['user_constraints']['model_selection']['libraries']}\n\n"

    toon_str += "#  MODEL_TUNING_STRATEGY\n"
    toon_str += f"search_type: {metadata['user_constraints']['tuning_strategy']['search_type']}\n"
    toon_str += f"max_trials: 2\n"
    toon_str += f"timeout: 60\n"

    with open("toon_s2_prompt.txt", "w", encoding="utf-8") as f:
        f.write(toon_str)
    return toon_str

def build_toon_payload(metadata, analysis_results, sample_df, features, target_meta):
    # 1. Metadatos Globales
    toon_str = "# GLOBAL_METADATA\n"
    toon_str += f"total_rows: {metadata['n_rows']}\n"
    # Si 'targets' es una lista, la usamos directo; si es dict, .keys()
    targets_list = metadata['targets'] if isinstance(metadata['targets'], list) else list(metadata['targets'].keys())
    toon_str += f"targets: {targets_list}\n"
    if len(targets_list) > 1:
        toon_str += "sampling_strategy: Stratified_MultiTarget_Combined\n\n"
    else:
        toon_str += "sampling_strategy: Stratified_SingleTarget\n\n"

    # 2. Muestra Representativa (Markdown)
    toon_str += "# REPRESENTATIVE_SAMPLE_100\n"
    # .to_markdown() es vital para que la IA entienda la estructura de tabla
    toon_str += sample_df.to_markdown(index=False) + "\n\n"

    # 3. Evaluación de Columnas
    toon_str += "# CATEGORICAL_SUBCLASS_EVALUATION\n"
    col = {}
    for col, info in analysis_results.items():
        # Solo enviamos las que el LLM debe clasificar (Niveles 1 y 2)
        if info.get("technical_level") in [1, 2]:
            toon_str += f"{col}:\n"
            toon_str += f"  technical_level: {info['technical_level']}\n"
            toon_str += f"  ig_scores: {info['information_gain']}\n"
            # Limitamos el pool para no saturar de texto el prompt
            toon_str += f"  unique_pool: {info['unique_pool'][:15]}\n"
            toon_str += f"  user_mandatory: {info.get('user_mandatory', False)}\n\n"
    
    toon_str += "# TARGETS_SUBCLASS_EVALUATION\n"
    targ = {}
    for targ, info in target_meta.items():
        # Solo enviamos las que el LLM debe clasificar (Niveles 1 y 2)
        if info.get("technical_level") in [1, 2]:
            toon_str += f"{targ}:\n"
            toon_str += f"  technical_level: {info['technical_level']}\n"

    dossier = {
        "global_metadata": {
            "total_rows": metadata['n_rows'],
            "features": len(features),
            "targets": targets_list,
            "sampling_strategy": "Stratified_MultiTarget_Combined" if len(targets_list) > 1 else "Stratified_SingleTarget"
        },
        "categorical_evaluation": {
            col: {
                "technical_level": info['technical_level'],
                "ig_scores": info['information_gain'],
                "unique_pool": info['unique_pool'][:15],
                "user_mandatory": info.get('user_mandatory', False)
            } for col, info in analysis_results.items() if info.get("technical_level") in [1, 2]
        },
        "targets_evaluation": {
            targ: {
                "technical_level": info['technical_level'],
            } for targ, info in target_meta.items() if info.get("technical_level") in [1, 2]
        }
    }

    with open("toon_dossier.json", "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=4, ensure_ascii=False)
        
    return toon_str


def integrar_analisis_llm(json_tecnico, respuesta_llm):
    """
    Extrae subclass, mapping y reasoning inyectándolos en las secciones 
    correspondientes (features y targets) del JSON técnico.
    """
    
    # 1. Patrón mejorado para capturar bloques de cualquier tipo (feature o target)
    # Este patrón busca el nombre seguido de sus 3 atributos clave
    patron = r"(\w+):\s*subclass:\s*(\w+)\s*mapping:\s*([^\n]+)\s*reasoning:\s*([^\n]+)"
    
    hallazgos = re.findall(patron, respuesta_llm)
    
    for nombre, subclass, mapping, reasoning in hallazgos:
        # Limpieza de valores
        subclass_clean = subclass.strip()
        reasoning_clean = reasoning.strip()
        val_mapping = mapping.strip()
        final_mapping = None if val_mapping.lower() == "null" else val_mapping

        # 2. Intentamos inyectar en CATEGORICAL_EVALUATION (Features)
        if nombre in json_tecnico.get("categorical_evaluation", {}):
            item = json_tecnico["categorical_evaluation"][nombre]
            item["subclass"] = subclass_clean
            item["mapping"] = final_mapping
            item["reasoning"] = reasoning_clean

        # 3. Intentamos inyectar en TARGETS_EVALUATION (Targets)
        elif nombre in json_tecnico.get("targets_evaluation", {}):
            item = json_tecnico["targets_evaluation"][nombre]
            item["subclass"] = subclass_clean
            item["mapping"] = final_mapping
            item["reasoning"] = reasoning_clean

    return json_tecnico
