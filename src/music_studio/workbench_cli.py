"""Independent workstation entry point; shared engine retains its import namespace."""
import sys

from .cli import main as engine_main


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["ui", "--open"]
    if args[0] == "ui":
        for flag, value in (("--interface", "create"), ("--port", "8920"),
                            ("--workspace", "outputs/workbench")):
            if flag not in args and not any(a.startswith(flag + "=") for a in args):
                args.extend((flag, value))
    return engine_main(args)
