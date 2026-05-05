"""CLI utility to test settings reactivity in eShelf."""

import argparse

from src.config import load_config, save_config


def main():
    parser = argparse.ArgumentParser(description="Test eShelf settings reactivity.")
    parser.add_argument("--cols", type=int, help="Number of books per line")
    parser.add_argument("--zoom", type=float, help="Zoom level for covers")
    args = parser.parse_args()

    config = load_config()

    changed = False
    if args.cols:
        config["books_per_line"] = args.cols
        changed = True
        print(f"Set books_per_line to: {args.cols}")

    if args.zoom:
        config["zoom_level"] = args.zoom
        changed = True
        print(f"Set zoom_level to: {args.zoom}")

    if changed:
        save_config(config)
        print(
            "Config saved. Please restart the app or trigger a reload to see changes."
        )
    else:
        print("No changes specified.")


if __name__ == "__main__":
    main()
