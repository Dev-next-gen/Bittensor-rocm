def run(args):
    from bittensor_wallet import Wallet
    import os

    wallet_name = args.wallet_name if hasattr(args, 'wallet_name') and args.wallet_name else "default"

    if args.wallet_command == "list":
        wallets_path = os.path.expanduser("~/.bittensor/wallets")
        if os.path.exists(wallets_path):
            print("\nAvailable wallets:")
            for wallet_dir in os.listdir(wallets_path):
                print(f" - {wallet_dir}")
        else:
            print("\nNo wallets found.")

    elif args.wallet_command == "new-coldkey":
        wallet = Wallet(name=wallet_name)
        wallet.create_new_coldkey()
        print(f"\nColdkey created: {wallet_name}")

    elif args.wallet_command == "new-hotkey":
        hotkey_name = args.wallet_hotkey if hasattr(args, 'wallet_hotkey') and args.wallet_hotkey else "default"
        wallet = Wallet(name=wallet_name)
        wallet.create_new_hotkey(name=hotkey_name)
        print(f"\nHotkey '{hotkey_name}' created for wallet '{wallet_name}'.")

    elif args.wallet_command == "regen-coldkey":
        wallet = Wallet(name=wallet_name)
        wallet.regenerate_coldkey()
        print(f"\nColdkey regenerated: {wallet_name}")

    else:
        print("Unknown wallet command.")
