
import re
import json

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


import re
import json

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