import argparse
from .csv_loader import load_groups
from .creator import run

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/groups.csv")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    rows = load_groups(args.csv)
    run(rows, headless=args.headless)

if __name__ == "__main__":
    main()