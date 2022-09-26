import argparse
import os

from twister2.platform_specification import search_platforms
from twister2.scripts.hardware_map import scan, write_to_file, print_hardware_map


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--generate-hardware-map',
        dest='hardware_map_path',
        metavar='path',
        help='generate hardware map',
    )
    parser.add_argument(
        '--list-hardware-map',
        dest='list_hardware_map',
        action='store_true',
        help='list hardware map',
    )
    parser.add_argument(
        '--list-default-platforms',
        dest='list_default_platforms',
        action='store_true',
        help='list default platforms',
    )
    args = parser.parse_args()

    if args.hardware_map_path:
        hardware_map_list = scan(persistent=False)
        write_to_file(hardware_map_list=hardware_map_list, filename=args.hardware_map_path)
        print_hardware_map(hardware_map_list)
        return 0
    if args.list_hardware_map:
        hardware_map_list = scan(persistent=False)
        print_hardware_map(hardware_map_list)
        return 0
    if args.list_default_platforms:
        zephyr_base = os.environ['ZEPHYR_BASE']
        platforms = search_platforms(zephyr_base=zephyr_base)
        for platform in platforms:
            print(platform.identifier)
        return 0

    parser.print_help()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
