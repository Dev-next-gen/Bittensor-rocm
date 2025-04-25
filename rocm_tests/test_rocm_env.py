"""
Validation de l'environnement ROCm (hip) sans CUDA.
"""

import torch
from bittensor.utils.torch_utils import is_gpu_available


def test_torch_runtime_has_hip():
    assert hasattr(torch.version, 'hip'), "ROCm (hip) non détecté"


def test_cuda_is_disabled():
    assert torch.cuda.is_available() is False, "CUDA ne doit pas être activé"


def test_wrapper_detects_hip():
    assert is_gpu_available() is True, "is_gpu_available() doit détecter ROCm"