import torch
import logging

def is_gpu_available():
    try:
        cuda_available = torch.cuda.is_available()
        rocm_available = torch.version.hip is not None
        available = cuda_available or rocm_available
        if available:
            logging.info(f"GPU available: {'CUDA' if cuda_available else 'ROCm'}")
        else:
            logging.warning("No ROCm or CUDA device detected. Falling back to CPU.")
        return available
    except Exception as e:
        logging.error(f"Error checking GPU availability: {e}")
        return False
