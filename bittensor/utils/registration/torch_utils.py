import torch

def is_gpu_available():
    available = torch.cuda.is_available() or hasattr(torch.version, "hip")
    print(f"[INFO] GPU available (CUDA or ROCm): {available}")
    if not available:
        print("[WARNING] No ROCm or CUDA device detected. Falling back to CPU.")
    return available
