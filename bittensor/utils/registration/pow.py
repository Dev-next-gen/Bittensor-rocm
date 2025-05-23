"""This module provides utilities for solving Proof-of-Work (PoW) challenges in Bittensor network."""
import binascii
import functools
import hashlib
import math
import multiprocessing as mp
import os
import random
import subprocess
import time
from dataclasses import dataclass
from datetime import timedelta
from multiprocessing.queues import Queue as QueueType
from queue import Empty, Full
from typing import Callable, Optional, Union, TYPE_CHECKING

import numpy
from Crypto.Hash import keccak

from bittensor.utils.btlogging import logging
from bittensor.utils.formatting import get_human_readable, millify
from bittensor.utils.torch_utils import is_gpu_available

def use_torch() -> bool:
    """Force the use of torch over numpy for certain operations."""
    return True if os.getenv("USE_TORCH") == "1" else False

def legacy_torch_api_compat(func):
    """
    Convert function operating on numpy Input&Output to legacy torch Input&Output API if `use_torch()` is True.
    Args:
        func (function): Function with numpy Input/Output to be decorated.
    Returns:
        decorated (function): Decorated function.
    """
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        if use_torch():
            args = [
                arg.cpu().numpy() if isinstance(arg, torch.Tensor) else arg
                for arg in args
            ]
            kwargs = {
                key: value.cpu().numpy() if isinstance(value, torch.Tensor) else value
                for key, value in kwargs.items()
            }
        ret = func(*args, **kwargs)
        if use_torch():
            if isinstance(ret, numpy.ndarray):
                ret = torch.from_numpy(ret)
        return ret
    return decorated

@functools.cache
def _get_real_torch():
    try:
        import torch as _real_torch
    except ImportError:
        _real_torch = None
    return _real_torch

def log_no_torch_error():
    logging.error("This command requires torch. You can install torch for bittensor with `pip install bittensor[torch]` or `pip install \".[torch]\"` if installing from source, and then run the command with USE_TORCH=1 {command}")

class LazyLoadedTorch:
    """A lazy-loading proxy for the torch module."""
    def __bool__(self):
        return bool(_get_real_torch())

    def __getattr__(self, name):
        if real_torch := _get_real_torch():
            return getattr(real_torch, name)
        else:
            log_no_torch_error()
            raise ImportError("torch not installed")

if TYPE_CHECKING:
    import torch
    from bittensor.core.subtensor import Subtensor
    from bittensor.core.async_subtensor import AsyncSubtensor
    from bittensor_wallet import Wallet
else:
    torch = LazyLoadedTorch()

def _hex_bytes_to_u8_list(hex_bytes: bytes) -> list[int]:
    return [int(hex_bytes[i: i + 2], 16) for i in range(0, len(hex_bytes), 2)]

def _create_seal_hash(block_and_hotkey_hash_bytes: bytes, nonce: int) -> bytes:
    nonce_bytes = binascii.hexlify(nonce.to_bytes(8, "little"))
    pre_seal = nonce_bytes + binascii.hexlify(block_and_hotkey_hash_bytes)[:64]
    seal_sh256 = hashlib.sha256(bytearray(_hex_bytes_to_u8_list(pre_seal))).digest()
    kec = keccak.new(digest_bits=256)
    seal = kec.update(seal_sh256).digest()
    return seal

def _seal_meets_difficulty(seal: bytes, difficulty: int, limit: int) -> bool:
    seal_number = int.from_bytes(seal, "big")
    product = seal_number * difficulty
    return product < limit

@dataclass
class POWSolution:
    """A solution to the registration PoW problem."""
    nonce: int
    block_number: int
    difficulty: int
    seal: bytes

    def is_stale(self, subtensor: "Subtensor") -> bool:
        return self.block_number < subtensor.get_current_block() - 3

    async def is_stale_async(self, subtensor: "AsyncSubtensor") -> bool:
        current_block = await subtensor.substrate.get_block_number(None)
        return self.block_number < current_block - 3

class UsingSpawnStartMethod:
    def __init__(self, force: bool = False):
        self._old_start_method = None
        self._force = force

    def __enter__(self):
        self._old_start_method = mp.get_start_method(allow_none=True)
        if self._old_start_method is None:
            self._old_start_method = "spawn"
        mp.set_start_method(self._old_start_method, force=self._force)

    def __exit__(self, *args):
        mp.set_start_method(self._old_start_method, force=True)

class _SolverBase(mp.Process):
    proc_num: int
    num_proc: int
    update_interval: int
    finished_queue: "mp.Queue"
    solution_queue: "mp.Queue"
    newBlockEvent: "mp.Event"
    stopEvent: "mp.Event"
    hotkey_bytes: bytes
    curr_block: "mp.Array"
    curr_block_num: "mp.Value"
    curr_diff: "mp.Array"
    check_block: "mp.Lock"
    limit: int

    def __init__(
        self,
        proc_num,
        num_proc,
        update_interval,
        finished_queue,
        solution_queue,
        stopEvent,
        curr_block,
        curr_block_num,
        curr_diff,
        check_block,
        limit,
    ):
        mp.Process.__init__(self, daemon=True)
        self.proc_num = proc_num
        self.num_proc = num_proc
        self.update_interval = update_interval
        self.finished_queue = finished_queue
        self.solution_queue = solution_queue
        self.newBlockEvent = mp.Event()
        self.newBlockEvent.clear()
        self.curr_block = curr_block
        self.curr_block_num = curr_block_num
        self.curr_diff = curr_diff
        self.check_block = check_block
        self.stopEvent = stopEvent
        self.limit = limit

    def run(self):
        raise NotImplementedError("_SolverBase is an abstract class")

    @staticmethod
    def create_shared_memory() -> tuple["mp.Array", "mp.Value", "mp.Array"]:
        curr_block = mp.Array("h", 32, lock=True)
        curr_block_num = mp.Value("i", 0, lock=True)
        curr_diff = mp.Array("Q", [0, 0], lock=True)
        return curr_block, curr_block_num, curr_diff

class CPUSolver(_SolverBase):
    def run(self):
        block_number: int
        block_and_hotkey_hash_bytes: bytes
        block_difficulty: int
        nonce_limit = int(math.pow(2, 64)) - 1
        
        nonce_start = random.randint(0, nonce_limit)
        nonce_end = nonce_start + self.update_interval
        
        while not self.stopEvent.is_set():
            if self.newBlockEvent.is_set():
                with self.check_block:
                    block_number = self.curr_block_num.value
                    block_and_hotkey_hash_bytes = bytes(self.curr_block)
                    block_difficulty = _registration_diff_unpack(self.curr_diff)
                self.newBlockEvent.clear()

            solution = _solve_for_nonce_block(
                nonce_start,
                nonce_end,
                block_and_hotkey_hash_bytes,
                block_difficulty,
                self.limit,
                block_number,
            )
            
            if solution is not None:
                self.solution_queue.put(solution)
                try:
                    self.finished_queue.put_nowait(self.proc_num)
                except Full:
                    pass

            nonce_start = random.randint(0, nonce_limit)
            nonce_start = nonce_start % nonce_limit
            nonce_end = nonce_start + self.update_interval

class GPUSolver(_SolverBase):
    def __init__(
        self,
        proc_num,
        num_proc,
        update_interval,
        finished_queue,
        solution_queue,
        stopEvent,
        curr_block,
        curr_block_num,
        curr_diff,
        check_block,
        limit,
        dev_id: int = 0,
        tpb: int = 256,
    ):
        super().__init__(
            proc_num,
            num_proc,
            update_interval,
            finished_queue,
            solution_queue,
            stopEvent,
            curr_block,
            curr_block_num,
            curr_diff,
            check_block,
            limit,
        )
        self.dev_id = dev_id
        self.tpb = tpb

    def run(self):
        block_number: int = 0
        block_and_hotkey_hash_bytes: bytes = b"0" * 32
        block_difficulty: int = int(math.pow(2, 64)) - 1
        nonce_limit = int(math.pow(2, 64)) - 1

        nonce_start = random.randint(0, nonce_limit)
        while not self.stopEvent.is_set():
            if self.newBlockEvent.is_set():
                with self.check_block:
                    block_number = self.curr_block_num.value
                    block_and_hotkey_hash_bytes = bytes(self.curr_block)
                    block_difficulty = _registration_diff_unpack(self.curr_diff)
                self.newBlockEvent.clear()

            solution = _solve_for_nonce_block_gpu(
                nonce_start,
                self.update_interval,
                block_and_hotkey_hash_bytes,
                block_difficulty,
                self.limit,
                block_number,
                self.dev_id,
                self.tpb,
            )
            
            if solution is not None:
                self.solution_queue.put(solution)

            try:
                self.finished_queue.put(self.proc_num)
            except Full:
                pass

            nonce_start += self.update_interval * self.tpb
            nonce_start = nonce_start % nonce_limit

def _solve_for_nonce_block(
    nonce_start: int,
    nonce_end: int,
    block_and_hotkey_hash_bytes: bytes,
    difficulty: int,
    limit: int,
    block_number: int,
) -> Optional["POWSolution"]:
    for nonce in range(nonce_start, nonce_end):
        seal = _create_seal_hash(block_and_hotkey_hash_bytes, nonce)
        if _seal_meets_difficulty(seal, difficulty, limit):
            return POWSolution(nonce, block_number, difficulty, seal)
    return None

def _solve_for_nonce_block_gpu(
    nonce_start: int,
    update_interval: int,
    block_and_hotkey_hash_bytes: bytes,
    difficulty: int,
    limit: int,
    block_number: int,
    dev_id: int,
    tpb: int,
) -> Optional["POWSolution"]:
    if not is_gpu_available():
        return None
        
    try:
        import torch
        solution = torch.ops.bittensor_helpers.solve_blocks(
            nonce_start,
            update_interval,
            block_and_hotkey_hash_bytes,
            difficulty,
            limit,
            block_number,
            dev_id,
            tpb,
        )
        if solution != -1:
            seal = _create_seal_hash(block_and_hotkey_hash_bytes, solution)
            return POWSolution(solution, block_number, difficulty, seal)
    except Exception as e:
        logging.warning(f"GPU solving failed: {e}")
    return None

def _registration_diff_unpack(packed_diff: "mp.Array") -> int:
    return int(packed_diff[0] << 32 | packed_diff[1])

def _registration_diff_pack(diff: int, packed_diff: "mp.Array"):
    packed_diff[0] = diff >> 32
    packed_diff[1] = diff & 0xFFFFFFFF

def _hash_block_with_hotkey(block_bytes: bytes, hotkey_bytes: bytes) -> bytes:
    kec = keccak.new(digest_bits=256)
    kec = kec.update(bytearray(block_bytes + hotkey_bytes))
    return kec.digest()

def update_curr_block(
    curr_diff: "mp.Array",
    curr_block: "mp.Array",
    curr_block_num: "mp.Value",
    block_number: int,
    block_bytes: bytes,
    diff: int,
    hotkey_bytes: bytes,
    lock: "mp.Lock",
):
    with lock:
        curr_block_num.value = block_number
        block_and_hotkey_hash_bytes = _hash_block_with_hotkey(block_bytes, hotkey_bytes)
        for i in range(32):
            curr_block[i] = block_and_hotkey_hash_bytes[i]
        _registration_diff_pack(diff, curr_diff)

def get_cpu_count() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count()

@dataclass
class RegistrationStatistics:
    time_spent_total: float
    rounds_total: int
    time_average: float
    time_spent: float
    hash_rate_perpetual: float
    hash_rate: float
    difficulty: int
    block_number: int
    block_hash: str

def _get_block_with_retry(subtensor: "Subtensor", netuid: int) -> tuple[int, int, str]:
    block_number = subtensor.get_current_block()
    difficulty = 1_000_000 if netuid == -1 else subtensor.difficulty(netuid=netuid)
    block_hash = subtensor.get_block_hash(block_number)
    if block_hash is None:
        raise Exception("Network error. Could not connect to substrate to get block hash")
    if difficulty is None:
        raise ValueError("Chain error. Difficulty is None")
    return block_number, difficulty, block_hash

def _check_for_newest_block_and_update(
    subtensor: "Subtensor",
    netuid: int,
    old_block_number: int,
    hotkey_bytes: bytes,
    curr_diff: "mp.Array",
    curr_block: "mp.Array",
    curr_block_num: "mp.Value",
    update_curr_block_: "Callable",
    check_block: "mp.Lock",
    curr_stats: "RegistrationStatistics",
    solvers: list[_SolverBase],
) -> int:
    block_number = subtensor.get_current_block()
    if block_number != old_block_number:
        old_block_number = block_number
        block_number, difficulty, block_hash = _get_block_with_retry(
            subtensor=subtensor, netuid=netuid
        )
        block_bytes = bytes.fromhex(block_hash[2:])

        update_curr_block_(
            curr_diff,
            curr_block,
            curr_block_num,
            block_number,
            block_bytes,
            difficulty,
            hotkey_bytes,
            check_block,
        )

        for worker in solvers:
            worker.newBlockEvent.set()

        curr_stats.block_number = block_number
        curr_stats.block_hash = block_hash
        curr_stats.difficulty = difficulty

    return old_block_number

def _solve_for_difficulty_fast(
    subtensor: "Subtensor",
    wallet: "Wallet",
    netuid: int,
    output_in_place: bool = True,
    num_processes: Optional[int] = None,
    update_interval: Optional[int] = None,
    n_samples: int = 10,
    alpha_: float = 0.80,
    log_verbose: bool = False,
) -> Optional[POWSolution]:
    if num_processes is None:
        num_processes = min(1, get_cpu_count())

    if update_interval is None:
        update_interval = 50_000

    limit = int(math.pow(2, 256)) - 1
    curr_block, curr_block_num, curr_diff = _SolverBase.create_shared_memory()

    stopEvent = mp.Event()
    stopEvent.clear()
    solution_queue = mp.Queue()
    finished_queues = [mp.Queue() for _ in range(num_processes)]
    check_block = mp.Lock()

    hotkey_bytes = (
        wallet.coldkeypub.public_key if netuid == -1 else wallet.hotkey.public_key
    )

    solvers = [
        CPUSolver(
            i,
            num_processes,
            update_interval,
            finished_queues[i],
            solution_queue,
            stopEvent,
            curr_block,
            curr_block_num,
            curr_diff,
            check_block,
            limit,
        )
        for i in range(num_processes)
    ]

    block_number, difficulty, block_hash = _get_block_with_retry(
        subtensor=subtensor, netuid=netuid
    )
    block_bytes = bytes.fromhex(block_hash[2:])
    old_block_number = block_number

    update_curr_block(
        curr_diff,
        curr_block,
        curr_block_num,
        block_number,
        block_bytes,
        difficulty,
        hotkey_bytes,
        check_block,
    )

    for worker in solvers:
        worker.newBlockEvent.set()
        worker.start()

    start_time = time.time()
    time_last = start_time

    curr_stats = RegistrationStatistics(
        time_spent_total=0.0,
        time_average=0.0,
        rounds_total=0,
        time_spent=0.0,
        hash_rate_perpetual=0.0,
        hash_rate=0.0,
        difficulty=difficulty,
        block_number=block_number,
        block_hash=block_hash,
    )

    start_time_perpetual = time.time()
    hash_rates = [0] * n_samples
    weights = [alpha_**i for i in range(n_samples)]

    solution = None
    while netuid == -1 or not subtensor.is_hotkey_registered(
        netuid=netuid, hotkey_ss58=wallet.hotkey.ss58_address
    ):
        try:
            solution = solution_queue.get(block=True, timeout=0.25)
            if solution is not None:
                break
        except Empty:
            pass

        old_block_number = _check_for_newest_block_and_update(
            subtensor=subtensor,
            netuid=netuid,
            hotkey_bytes=hotkey_bytes,
            old_block_number=old_block_number,
            curr_diff=curr_diff,
            curr_block=curr_block,
            curr_block_num=curr_block_num,
            curr_stats=curr_stats,
            update_curr_block_=update_curr_block,
            check_block=check_block,
            solvers=solvers,
        )

        num_time = 0
        for finished_queue in finished_queues:
            try:
                finished_queue.get(timeout=0.1)
                num_time += 1
            except Empty:
                continue

        time_now = time.time()
        time_since_last = time_now - time_last
        if num_time > 0 and time_since_last > 0.0:
            hash_rate_ = (num_time * update_interval) / time_since_last
            hash_rates.append(hash_rate_)
            hash_rates.pop(0)
            curr_stats.hash_rate = sum(
                [hash_rates[i] * weights[i] for i in range(n_samples)]
            ) / (sum(weights))

            time_last = time_now
            curr_stats.time_average = (
                curr_stats.time_average * curr_stats.rounds_total
                + curr_stats.time_spent
            ) / (curr_stats.rounds_total + num_time)
            curr_stats.rounds_total += num_time

        curr_stats.time_spent = time_since_last
        new_time_spent_total = time_now - start_time_perpetual
        curr_stats.hash_rate_perpetual = (
            curr_stats.rounds_total * update_interval
        ) / new_time_spent_total
        curr_stats.time_spent_total = new_time_spent_total

    stopEvent.set()
    terminate_workers_and_wait_for_exit(solvers)
    return solution

def _solve_for_difficulty_gpu(
    subtensor: "Subtensor",
    wallet: "Wallet",
    netuid: int,
    output_in_place: bool = True,
    dev_id: Union[list[int], int] = 0,
    tpb: int = 256,
    update_interval: Optional[int] = None,
    n_samples: int = 10,
    alpha_: float = 0.80,
    log_verbose: bool = False,
) -> Optional[POWSolution]:
    if isinstance(dev_id, int):
        dev_id = [dev_id]
    elif dev_id is None:
        dev_id = [0]

    if update_interval is None:
        update_interval = 50_000

    if not is_gpu_available():
        raise Exception("GPU not available")

    limit = int(math.pow(2, 256)) - 1

    with UsingSpawnStartMethod(force=True):
        num_processes = len(dev_id)
        curr_block, curr_block_num, curr_diff = _SolverBase.create_shared_memory()

        stopEvent = mp.Event()
        stopEvent.clear()
        solution_queue = mp.Queue()
        finished_queues = [mp.Queue() for _ in range(num_processes)]
        check_block = mp.Lock()

        hotkey_bytes = wallet.coldkeypub.public_key if netuid == -1 else wallet.hotkey.public_key
        solvers = [
            GPUSolver(
                i,
                num_processes,
                update_interval,
                finished_queues[i],
                solution_queue,
                stopEvent,
                curr_block,
                curr_block_num,
                curr_diff,
                check_block,
                limit,
                dev_id[i],
                tpb,
            )
            for i in range(num_processes)
        ]

        block_number, difficulty, block_hash = _get_block_with_retry(
            subtensor=subtensor, netuid=netuid
        )
        block_bytes = bytes.fromhex(block_hash[2:])
        old_block_number = block_number

        update_curr_block(
            curr_diff,
            curr_block,
            curr_block_num,
            block_number,
            block_bytes,
            difficulty,
            hotkey_bytes,
            check_block,
        )

        for worker in solvers:
            worker.newBlockEvent.set()
            worker.start()

        start_time = time.time()
        time_last = start_time

        curr_stats = RegistrationStatistics(
            time_spent_total=0.0,
            time_average=0.0,
            rounds_total=0,
            time_spent=0.0,
            hash_rate_perpetual=0.0,
            hash_rate=0.0,
            difficulty=difficulty,
            block_number=block_number,
            block_hash=block_hash,
        )

        start_time_perpetual = time.time()
        hash_rates = [0] * n_samples
        weights = [alpha_**i for i in range(n_samples)]

        solution = None
        while netuid == -1 or not subtensor.is_hotkey_registered(
            netuid=netuid, hotkey_ss58=wallet.hotkey.ss58_address
        ):
            try:
                solution = solution_queue.get(block=True, timeout=0.15)
                if solution is not None:
                    break
            except Empty:
                pass

            old_block_number = _check_for_newest_block_and_update(
                subtensor=subtensor,
                netuid=netuid,
                hotkey_bytes=hotkey_bytes,
                old_block_number=old_block_number,
                curr_diff=curr_diff,
                curr_block=curr_block,
                curr_block_num=curr_block_num,
                curr_stats=curr_stats,
                update_curr_block_=update_curr_block,
                check_block=check_block,
                solvers=solvers,
            )

            num_time = 0
            for finished_queue in finished_queues:
                try:
                    finished_queue.get(timeout=0.1)
                    num_time += 1
                except Empty:
                    continue

            time_now = time.time()
            time_since_last = time_now - time_last
            if num_time > 0 and time_since_last > 0.0:
                hash_rate_ = (num_time * tpb * update_interval) / time_since_last
                hash_rates.append(hash_rate_)
                hash_rates.pop(0)
                curr_stats.hash_rate = sum(
                    [hash_rates[i] * weights[i] for i in range(n_samples)]
                ) / (sum(weights))

                time_last = time_now
                curr_stats.time_average = (
                    curr_stats.time_average * curr_stats.rounds_total
                    + curr_stats.time_spent
                ) / (curr_stats.rounds_total + num_time)
                curr_stats.rounds_total += num_time

            curr_stats.time_spent = time_since_last
            new_time_spent_total = time_now - start_time_perpetual
            curr_stats.hash_rate_perpetual = (
                curr_stats.rounds_total * (tpb * update_interval)
            ) / new_time_spent_total
            curr_stats.time_spent_total = new_time_spent_total

        stopEvent.set()
        terminate_workers_and_wait_for_exit(solvers)
        return solution

def terminate_workers_and_wait_for_exit(
    workers: list[Union[mp.Process, QueueType]],
) -> None:
    for worker in workers:
        if isinstance(worker, QueueType):
            worker.join_thread()
        else:
            try:
                worker.join(3.0)
            except subprocess.TimeoutExpired:
                worker.terminate()
        try:
            worker.close()
        except ValueError:
            worker.terminate()

def create_pow(
    subtensor: "Subtensor",
    wallet: "Wallet",
    netuid: int,
    output_in_place: bool = True,
    cuda: bool = False,
    dev_id: Union[list[int], int] = 0,
    tpb: int = 256,
    num_processes: Optional[int] = None,
    update_interval: Optional[int] = None,
    log_verbose: bool = False,
) -> Optional["POWSolution"]:
    if netuid != -1 and not subtensor.subnet_exists(netuid=netuid):
        raise ValueError(f"Subnet {netuid} does not exist.")

    if cuda and is_gpu_available():
        return _solve_for_difficulty_gpu(
            subtensor,
            wallet,
            netuid=netuid,
            output_in_place=output_in_place,
            dev_id=dev_id,
            tpb=tpb,
            update_interval=update_interval,
            log_verbose=log_verbose,
        )
    else:
        return _solve_for_difficulty_fast(
            subtensor,
            wallet,
            netuid=netuid,
            output_in_place=output_in_place,
            num_processes=num_processes,
            update_interval=update_interval,
            log_verbose=log_verbose,
        )


async def create_pow_async(*args, **kwargs):
    return create_pow(*args, **kwargs)

