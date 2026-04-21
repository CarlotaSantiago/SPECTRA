def build_toon_payload(metadata, analysis_results, sample_df):
    # 1. Metadatos Globales
    toon_str = "# GLOBAL_METADATA\n"
    toon_str += f"total_rows: {metadata['n_rows']}\n"
    # Si 'targets' es una lista, la usamos directo; si es dict, .keys()
    targets_list = metadata['targets'] if isinstance(metadata['targets'], list) else list(metadata['targets'].keys())
    toon_str += f"targets: {targets_list}\n"
    toon_str += "sampling_strategy: Stratified_Proportional\n\n"

    # 2. Muestra Representativa (Markdown)
    toon_str += "# REPRESENTATIVE_SAMPLE_100\n"
    # .to_markdown() es vital para que la IA entienda la estructura de tabla
    toon_str += sample_df.to_markdown(index=False) + "\n\n"

    # 3. Evaluación de Columnas
    toon_str += "# CATEGORICAL_SUBCLASS_EVALUATION\n"
    for col, info in analysis_results.items():
        # Solo enviamos las que el LLM debe clasificar (Niveles 1 y 2)
        if info.get("technical_level") in [1, 2]:
            toon_str += f"{col}:\n"
            toon_str += f"  technical_level: {info['technical_level']}\n"
            toon_str += f"  ig_scores: {info['information_gain']}\n"
            # Limitamos el pool para no saturar de texto el prompt
            toon_str += f"  unique_pool: {info['unique_pool'][:15]}\n"
            toon_str += f"  user_mandatory: {info.get('user_mandatory', False)}\n\n"

    return toon_str