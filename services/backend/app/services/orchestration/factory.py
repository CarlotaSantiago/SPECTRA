"""
Módulo de factoría para la selección y construcción de estrategias de orquestación.

Implementa un patrón Factory que analiza las dependencias estadísticas y estructurales 
entre múltiples variables objetivo (targets) para instanciar la estrategia de modelado óptima: 
cadenas condicionales (Gated), independientes (MultiOutput), regresión lineal múltiple en cadena, 
clasificación multietiqueta en cadena o enfoques híbridos.
"""

import pandas as pd
from typing import Any

from .matrix import compute_threshold, compute_target_dependency_matrix
from .structural import detect_structural_absences, resolve_chain_order
from .strategies.base import OrchestrationStrategy
from .strategies.gated import GatedChainStrategy
from .strategies.multi_output import MultiOutputStrategy
from .strategies.regressor import RegressorChainStrategy
from .strategies.classifier import ClassifierChainStrategy
from .strategies.hybrid import HybridChainStrategy

def build_chain_strategy(df: pd.DataFrame, matrix: pd.DataFrame, tipos: dict, threshold_cfg: Any, toon_dossier: dict) -> OrchestrationStrategy:
    """
    Factory que evalúa las dependencias y retorna la estrategia de orquestación adecuada.
    
    Evalúa dinámicamente si el problema presenta ausencias estructurales (datos faltantes no aleatorios), 
    si las variables objetivo superan los umbrales de dependencia estadística mutua para justificar 
    un encadenamiento secuencial, y segmenta el flujo según la naturaleza técnica (categórica, 
    numérica o mixta) de los objetivos.
    """
    targets = matrix.index.tolist()
    threshold = compute_threshold(matrix, threshold_cfg)
    
    max_dep = float(matrix.where(matrix < 1.0).max().max()) if len(targets) > 1 else 0.0
    if pd.isna(max_dep): max_dep = 0.0
    
    # 1. Control de ausencias estructurales (MNAR)
    gated = detect_structural_absences(df, targets)
    if gated:
        gating = gated['gating']
        dependents = gated['dependents']
        print(f"Applying GatedChain strategy with gating variable '{gating}' and dependents {dependents}")
        subset_df = df[df[gated['gating']].notna()]
        sub_matrix = compute_target_dependency_matrix(subset_df, gated['dependents'], tipos)
        
        sub_strategy = build_chain_strategy(subset_df, sub_matrix, tipos, threshold_cfg, toon_dossier)
        return GatedChainStrategy(gating=gating, dependents=dependents, max_dependency=max_dep, sub_strategy=sub_strategy)

    # 2. Objetivos independientes
    if max_dep < threshold:
        return MultiOutputStrategy(order=targets, max_dependency=max_dep)

    order = resolve_chain_order(matrix, threshold)
    get_lvl = lambda t: tipos.get(t).get('technical_level') if isinstance(tipos.get(t), dict) else tipos.get(t)

    todos_cat = all(get_lvl(t) in (1, 2) for t in targets)
    todos_num = all(get_lvl(t) in (3, 4) for t in targets)
 
    # 3. Regressor Chain
    if todos_num:
        return RegressorChainStrategy(order=order, max_dependency=max_dep)

    # 4. Classifier Chain
    if todos_cat:
        semantic = toon_dossier.get('semantic_classification', {})
        target_profiles = {
            t: {
                'subclass':   semantic.get(t, {}).get('subclass', 'NOMINAL'),         
                'n_classes': int(df[t].nunique()),
                'mapping':    semantic.get(t, {}).get('mapping', None)         
            }
            for t in order
        }
        return ClassifierChainStrategy(order=order, target_profiles=target_profiles, max_dependency=max_dep)

    # 5. Hybrid Chain (Fallback)
    return HybridChainStrategy(order=order, max_dependency=max_dep)