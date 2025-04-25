from bittensor.utils.registration.pow import (
    create_pow,
    legacy_torch_api_compat,
    log_no_torch_error,
    torch,
    use_torch,
    LazyLoadedTorch,
    POWSolution,
)
from bittensor.utils.registration.async_pow import create_pow_async
from bittensor.utils.torch_utils import is_gpu_available  # Ajout pour ROCm

__all__ = [
    create_pow,
    legacy_torch_api_compat,
    log_no_torch_error,
    torch,
    use_torch,
    LazyLoadedTorch,
    POWSolution,
    create_pow_async,
    is_gpu_available,  # Ajouté
]