import argparse

import anim.log  # noqa: F401


def usage():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--verbose",
        action="store",
        help="verbose",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        default="INFO",
    )
    return parser.parse_args()


def app():
    args = usage()
    anim.log.create_logger(level=args.verbose)

    print("one simple command line")
