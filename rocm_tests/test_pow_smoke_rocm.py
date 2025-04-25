"""
Smoke-tests PoW synchrone et asynchrone en environnement ROCm.
"""
import pytest
from bittensor.utils.registration.pow import create_pow, POWSolution
from bittensor.utils.registration.async_pow import create_pow_async

# Simulations de Subtensor et Wallet minimalistes
class DummySubtensorSyn:
    def subnet_exists(self, netuid): return True
    def get_current_block(self): return 1
    def difficulty(self, netuid): return 1000
    def get_block_hash(self, block): return "0x" + "00"*32
    def is_hotkey_registered(self, **kw): return True

class DummySubtensorAsync(DummySubtensorSyn):
    async def subnet_exists(self, netuid): return True

class DummyWallet:
    class hotkey:
        ss58_address = "dummy"
    class coldkeypub:
        public_key = b""
    hotkey = hotkey()
    coldkeypub = coldkeypub()


def test_create_pow_smoke():
    sol = create_pow(DummySubtensorSyn(), DummyWallet(), netuid=-1)
    assert isinstance(sol, POWSolution) or sol is None

@pytest.mark.asyncio
async def test_create_pow_async_smoke():
    sol = await create_pow_async(DummySubtensorAsync(), DummyWallet(), netuid=-1)
    assert isinstance(sol, POWSolution) or sol is None