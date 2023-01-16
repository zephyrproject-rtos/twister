import argparse
import os

from twister2.platform_specification import search_platforms
from twister2.scripts.hardware_map import print_hardware_map, scan, write_to_file


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    hardware_subparser = subparsers.add_parser('hardware-map', help='hardware map')
    meg = hardware_subparser.add_mutually_exclusive_group()
    meg.add_argument(
        '-g', '--generate',
        dest='hardware_map_path',
        metavar='PATH',
        help='generate hardware map',
    )
    meg.add_argument(
        '-l', '--list',
        dest='list_hardware_map',
        action='store_true',
        help='list hardware map',
    )
    hardware_subparser.add_argument(
        '--persistent',
        dest='persistent',
        action='store_true',
        help='Use persistent for searching hardware',
    )

    platforms_subparser = subparsers.add_parser('platforms', help='platforms')
    platforms_subparser.add_argument(
        '-l', '--list',
        dest='list_platforms',
        action='store_true',
        help='list all available platforms',
    )
    platforms_subparser.add_argument(
        '--default-only',
        dest='default_only',
        action='store_true',
        help='only default platforms',
    )

    args = parser.parse_args()

    if args.command == 'hardware-map':
        if args.hardware_map_path:
            hardware_map_list = scan(persistent=args.persistent)
            write_to_file(hardware_map_list=hardware_map_list, filename=args.hardware_map_path)
            print_hardware_map(hardware_map_list)
            return 0
        elif args.list_hardware_map:
            hardware_map_list = scan(persistent=args.persistent)
            print_hardware_map(hardware_map_list)
            return 0
        else:
            hardware_subparser.print_help()
            return -1
    elif args.command == 'platforms':
        if args.list_platforms:
            zephyr_base = os.environ['ZEPHYR_BASE']
            platforms = search_platforms(zephyr_base=zephyr_base, default_only=args.default_only)
            for platform in platforms:
                print(platform.identifier)
            print(f'\nTotal: {len(platforms)}')
            return 0
        else:
            platforms_subparser.print_help()
            return -1

    parser.print_help()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
