#!/usr/bin/env python3
import argparse
import sys
from Anime3rbDL import Anime3rbDL

def parse_args():
    parser = argparse.ArgumentParser(
        prog="Anime3rbDL",
        description=f"Anime3rbDL - Download Anime from: [{Anime3rbDL.WebsiteURL}] - Made With ♥ By: Mr.Jo0x01",
        epilog="Example: Anime3rbDL 'Naruto' --res 720 --download"
    )

    parser.add_argument(
        "query",
        metavar="SEARCH_OR_URL",
        help="Search query or Anime URL (required)"
    )
    parser.add_argument(
        "--download-parts",
        metavar="RANGE",
        default="all",
        help="Download specific episodes (e.g., 1-3). Default: all"
    )
    parser.add_argument(
        "--res",
        choices=["low", "mid", "high"],
        default="low",
        help="Resolution for info/download. Default: low"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Directory to save downloads. Default: current directory"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Automatically download after fetching info"
    )

    return parser.parse_args()

def main():
    args = parse_args()
    anime = Anime3rbDL()

    res = anime.DefaultResoultion.get(args.res)
    if res is None:
        sys.exit(f"[ERROR] Invalid resolution: {args.res}. Available: {list(anime.DefaultResoultion.keys())}")

    anime.search(args.query)
    if isinstance(anime.SearchResult, list) and len(anime.SearchResult) > 1:
        anime.show_search_data()
        try:
            choice = int(input("\nSelect anime by number: ")) - 1
            anime.search(anime.SearchResult[choice]["link"])
        except (ValueError, IndexError):
            sys.exit("[ERROR] Invalid selection.")

    anime.get_info(skip_parts=args.download_parts)
    anime.show_download_info(res=res)

    if args.download:
        proceed = input("\nStart download? [y/N]: ").strip().lower()
        if proceed in ("y", "yes"):
            anime.download(path=args.path, res=args.res)
            print("\n[INFO] Download completed successfully!")
        else:
            print("\n[INFO] Download cancelled.")
    print("\nThank you for using Anime3rbDL!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n[INFO] Operation cancelled by user.")
    except Exception as e:
        sys.exit(f"[ERROR] {e}")
