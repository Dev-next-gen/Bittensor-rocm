def run(args):
    from bittensor import metagraph as bt_metagraph

    if args.metagraph_command == "sync":
        metagraph = bt_metagraph(netuid=1, network="finney")
        metagraph.sync()
        print("\nMetagraph synchronized.")

    elif args.metagraph_command == "overview":
        metagraph = bt_metagraph(netuid=1, network="finney")
        metagraph.sync()
        print(f"\nMetagraph Overview:")
        print(f" - Number of neurons: {len(metagraph.axons)}")

    else:
        print("Unknown metagraph command.")
