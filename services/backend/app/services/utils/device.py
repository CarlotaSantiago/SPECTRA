"""
Módulo de detección autónoma y gestión de dispositivos de cómputo en PyTorch.

Permite identificar dinámicamente el mejor backend de hardware disponible (CUDA, MPS o CPU) 
para la ejecución de modelos de aprendizaje profundo, aplicando restricciones basadas en la 
disponibilidad de memoria de video (VRAM) libre con el fin de mitigar errores de Out Of Memory (OOM).
"""

import torch
# =============================================================================
# DEVICE DETECTION
# =============================================================================

def get_device(device_arg=None):
    """
    Determine the best available compute device.

    Priority order (when no explicit device is requested):
      1. CUDA GPU  - used only if at least 2 GB of free VRAM is available,
                     so that multiple large transformer models can coexist.
      2. Apple MPS - Metal Performance Shaders on Apple Silicon (M1/M2/M3).
      3. CPU       - fallback that always works, but is significantly slower.

    Args:
        device_arg: Optional string ('cuda', 'mps', or 'cpu') that bypasses
                    auto-detection and forces a specific device.

    Returns:
        A torch.device object ready to be passed to model.to().
    """
    if device_arg:
        # User explicitly chose a device; honour that without further checks.
        return torch.device(device_arg)

    if torch.cuda.is_available():
        # Check that there is enough free VRAM (minimum 2 GB per model).
        # Loading four large transformer models simultaneously can easily
        # consume 8-10 GB; 2 GB is a conservative lower bound for a single
        # model to load without triggering CUDA out-of-memory errors.
        free_mem = torch.cuda.mem_get_info()[0] / 1e9
        if free_mem >= 2.0:
            return torch.device("cuda")
        else:
            print(f"  GPU detected but free VRAM is not sufficient ({free_mem:.1f} GB).")
            print("  Using CPU instead.")

    # MPS is the GPU backend for Apple Silicon; it offers a significant
    # speed-up over CPU on M-series Macs.
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")