"""Print the az/alt angles the motors need. This is the only file that prints.

Run from the project root:

    python -m scripts.print_angles --target mars
    python -m scripts.print_angles --target jupiter --interval 5
    python -m scripts.print_angles --all --once
    python -m scripts.print_angles --list

(`-m` is used so that Python can find the `tracking` package.)
"""

from __future__ import annotations

import argparse
import time

from tracking import PointingCalculator, UnknownTargetError, default_catalog


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print telescope pointing angles.")
    parser.add_argument("--target", default="mars", help="target name (see --list)")
    parser.add_argument("--all", action="store_true", help="show every target")
    parser.add_argument("--list", action="store_true", help="list available targets and exit")
    parser.add_argument("--once", action="store_true", help="print once instead of looping")
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between updates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catalog = default_catalog()

    if args.list:
        print("\n".join(catalog.names()))
        return 0

    try:
        targets = (
            [catalog.get(name) for name in catalog.names()]
            if args.all
            else [catalog.get(args.target)]
        )
    except UnknownTargetError as error:
        print(error)
        return 1

    calculator = PointingCalculator()  # first run downloads the ephemeris
    cfg = calculator.config
    print(f"Site: lat {cfg.latitude_deg:.4f}, lon {cfg.longitude_deg:.4f}, "
          f"min altitude {cfg.min_altitude_deg}\N{DEGREE SIGN}")

    try:
        while True:
            pointings = calculator.compute_many(targets)
            print(pointings[0].timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
            for pointing in pointings:
                print("  ", pointing)
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())