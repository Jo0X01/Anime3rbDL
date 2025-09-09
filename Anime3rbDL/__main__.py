#!/usr/bin/env python3
import argparse
import sys
from Anime3rbDL import Anime3rbDL

def parse_args():
    parser = argparse.ArgumentParser(
        prog="Anime3rbDL",
        description=f"Anime3rbDL - Download Anime from: [{Anime3rbDL.WebsiteURL}] - Made With ♥ By: Mr.Jo0x01",
        epilog="Example: Anime3rbDL 'Naruto' --res low --download"
    )

    parser.add_argument(
        "query",
        metavar="SEARCH_OR_URL",
        help="Search query or Anime URL (required)"
    )
    parser.add_argument(
        "--download-parts",
        metavar="RANGE",
        default=None,
        help="Download specific episodes (example: 1-3). Default: all"
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
            choice = anime.SearchResult[int(input("Select anime by number >>> ")) - 1]
            print(f"[INFO] Chosen Anime: {choice['title']}")
            anime.search(choice["link"])
            if args.download_parts == None:
                args.download_parts = str(input("[INP] Provide Download Parts Range (example: 1-3) (Default: all): "))
        except (ValueError, IndexError):
            sys.exit("[ERROR] Invalid selection.")
    else:
        if args.download_parts == None:
            args.download_parts = "all"

    anime.get_info(download_parts=args.download_parts)
    anime.show_episodes_info()
    
    proceed = input(f"[INP] Start download in [{args.res}] Resolution  ? [y/N]: ").strip().lower()
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
