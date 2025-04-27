import sys
import argparse
import os
import subprocess

from bittensor import __version__
from bittensor.utils.version import check_latest_version_in_pypi

def main():
    parser = argparse.ArgumentParser(
        description="Bittensor SDK CLI - ROCm Edition 🧠🔥",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Display Bittensor SDK version"
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommands available")

    # Wallet subcommand
    wallet_parser = subparsers.add_parser("wallet", help="Manage wallets (coldkey, hotkeys)")
    wallet_parser.add_argument("wallet_command", choices=["new-coldkey", "new-hotkey", "list", "regen-coldkey"], help="Wallet operation")
    wallet_parser.add_argument("--wallet.name", type=str, help="Wallet name")
    wallet_parser.add_argument("--wallet.hotkey", type=str, help="Hotkey name")

    # Metagraph subcommand
    metagraph_parser = subparsers.add_parser("metagraph", help="Interact with Metagraph")
    metagraph_parser.add_argument("metagraph_command", choices=["sync", "overview"], help="Metagraph operation")

    args = parser.parse_args()

    if args.version:
        print(f"Bittensor SDK version: {__version__}")
        check_latest_version_in_pypi()
        return

    if args.command == "wallet":
        from bittensor.cli import wallet as wallet_cli
        wallet_cli.run(args)

    elif args.command == "metagraph":
        from bittensor.cli import metagraph as metagraph_cli
        metagraph_cli.run(args)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
