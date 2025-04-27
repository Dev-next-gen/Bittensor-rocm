import asyncio
from .pow import create_pow, POWSolution

async def create_pow_async(
    subtensor,
    wallet,
    netuid: int,
    output_in_place: bool = True,
    dev_id: int = 0,
    tpb: int = 256,
    update_interval: int = None,
    log_verbose: bool = False,
) -> POWSolution:
    loop = asyncio.get_event_loop()
    solution = await loop.run_in_executor(
        None,
        lambda: create_pow(
            subtensor=subtensor,
            wallet=wallet,
            netuid=netuid,
            output_in_place=output_in_place,
            dev_id=dev_id,
            tpb=tpb,
            update_interval=update_interval,
            log_verbose=log_verbose,
        ),
    )
    return solution
