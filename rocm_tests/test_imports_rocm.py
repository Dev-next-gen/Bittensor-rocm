"""
Tests d'import pour garantir que les modules fonctionnent en environnement ROCm.
"""

def test_import_torch_utils():
    from bittensor.utils.torch_utils import is_gpu_available
    assert callable(is_gpu_available)


def test_import_pow_and_async():
    from bittensor.utils.registration import pow, async_pow
    assert hasattr(pow, 'create_pow')
    assert hasattr(async_pow, 'create_pow_async')


def test_import_init_exports():
    import bittensor.utils as utils
    assert hasattr(utils, 'create_pow')
    assert hasattr(utils, 'create_pow_async')
    assert hasattr(utils, 'is_gpu_available')