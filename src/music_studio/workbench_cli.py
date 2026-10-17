"""Public Workbench commands; the internal engine keeps its historical namespace."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import Settings


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="music-workbench",
        description="Music Workbench: local composition, arrangement, recording and mixing.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Show Workbench runtime and GPU information")
    ui = commands.add_parser("ui", help="Open the music creation workspace")
    ui.add_argument("--workspace", type=Path, default=Path("outputs/workbench"))
    ui.add_argument("--port", type=int, default=8920)
    ui.add_argument("--open", action="store_true", dest="open_browser")
    ui.add_argument("--interface", choices=["create", "next"], default="create",
                    help="Creation workspace or single-asset editor")
    ui.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    ui.add_argument("--model-dir", type=Path, default=Path(Settings().model_dir))
    network = ui.add_mutually_exclusive_group()
    network.add_argument("--offline", action="store_true", dest="offline", default=True)
    network.add_argument("--online", action="store_false", dest="offline",
                         help="Allow configured model backends to access the network")
    ui.add_argument("--threads", type=int, default=4)
    ui.add_argument("--seed", type=int, default=0)
    ui.add_argument("--inference-python", type=Path, help="Explicit optional music-tool runtime")
    ui.add_argument("--lyrics-python", type=Path, help="Explicit optional transcription runtime")
    args = parser.parse_args(arguments or ["ui", "--open"])
    try:
        if args.command == "doctor":
            from .cli import doctor

            report = doctor()
            report["product"] = "music-workbench"
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        from .ui.server import serve

        settings = Settings(**{
            name: str(value) if isinstance(value, Path) else value
            for name, value in vars(args).items() if name in Settings.model_fields
        }).resolved()
        serve(args.workspace, settings, args.port, args.open_browser, args.interface)
    except KeyboardInterrupt:
        return 130
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f"Music Workbench: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
