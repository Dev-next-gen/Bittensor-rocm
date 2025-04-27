import asyncio
from bittensor_wallet import Wallet
from bittensor.core.metagraph import Metagraph
from bittensor.core.dendrite import Dendrite
from bittensor.core.synapse import Synapse

async def miner_test():
    print("[*] Loading wallet...")
    wallet = Wallet(name="Rig_1", hotkey="Server_1")
    print(f"[+] Wallet loaded: {wallet.hotkey.ss58_address}")

    print("[*] Connecting to Metagraph (Subnet 36)...")
    metagraph = Metagraph(netuid=36, network="finney")
    metagraph.sync()
    print(f"[+] Metagraph synchronized. Number of axons: {len(metagraph.axons)}")

    print("[*] Preparing Dendrite connection...")
    dendrite = Dendrite(wallet=wallet)
    axon = metagraph.axons[0]
    print(f"[+] Selected axon: {axon}")

    print("[*] Sending Synapse (Hello ROCm Miner)...")
    input_synapse = Synapse()
    response = await dendrite.forward(axon, input_synapse)

    print("[+] Response received:")
    print(response)

    # 🛠 Clean: Only close if method exists
    if hasattr(dendrite, "close") and callable(getattr(dendrite, "close")):
        print("[*] Closing Dendrite session...")
        await dendrite.close()
        print("[+] Session closed.")
    else:
        print("[*] No dendrite.close() method detected, skipping.")

    print("[+] Miner test completed successfully.")

if __name__ == "__main__":
    asyncio.run(miner_test())
