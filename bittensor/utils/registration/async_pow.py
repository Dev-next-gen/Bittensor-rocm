import asyncio
from typing import Optional, TYPE_CHECKING

from bittensor.utils.registration.pow import create_pow
from bittensor.utils.torch_utils import is_gpu_available

if TYPE_CHECKING:
    from bittensor.core.async_subtensor import AsyncSubtensor
    from bittensor_wallet import Wallet
    from bittensor.utils.registration import POWSolution

async def create_pow_async(
    subtensor: "AsyncSubtensor",
    wallet: "Wallet",
    netuid: int,
    output_in_place: bool = True,
    num_processes: Optional[int] = None,
    update_interval: Optional[int] = None,
    log_verbose: bool = False,
) -> "POWSolution":
    """
    Asynchronous wrapper pour créer un Proof-of-Work via create_pow.

    Args:
        subtensor (AsyncSubtensor): Client asynchrone pour Subtensor.
        wallet (Wallet): Wallet pour l'enregistrement.
        netuid (int): Identifiant du réseau.
        output_in_place (bool): Affichage en place.
        num_processes (int): Nombre de processus CPU.
        update_interval (int): Nombre de nonces avant mise à jour du bloc.
        log_verbose (bool): Mode verbeux.

    Returns:
        POWSolution: Solution PoW.

    Raises:
        ValueError: NetUID invalide.
        RuntimeError: Pas de GPU ROCm/CUDA détecté.
    """
    # Vérification du subnet
    if netuid != -1 and not await subtensor.subnet_exists(netuid=netuid):
        raise ValueError(f"Subnet {netuid} does not exist")

    # Vérification GPU ROCm/CUDA
    if not is_gpu_available():
        raise RuntimeError("No ROCm/CUDA device detected for PoW")

    loop = asyncio.get_running_loop()
    # Exécuter le solveur synchrone dans un thread séparé
    solution = await loop.run_in_executor(
        None,
        lambda: create_pow(
            subtensor=subtensor,
            wallet=wallet,
            netuid=netuid,
            output_in_place=output_in_place,
            cuda=False,
            dev_id=0,
            tpb=256,
            num_processes=num_processes,
            update_interval=update_interval,
            log_verbose=log_verbose,
        ),
    )
    return solution
