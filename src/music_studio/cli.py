import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

from . import __version__
from .config import Settings


def add_settings(parser):
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--model-dir", type=Path, default=Path(Settings().model_dir))
    parser.add_argument(
        "--asr-model", default=Settings().asr_model, help="Whisper size or a local model directory"
    )
    parser.add_argument(
        "--asr-revision", help="Hugging Face commit; small and large-v3-turbo are pinned"
    )
    parser.add_argument(
        "--separation-model", choices=["htdemucs", "htdemucs_ft"], default="htdemucs"
    )
    parser.add_argument("--offline", action="store_true", help="Use cached models; never download")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--asr-segmentation", choices=["whole", "vocal"], default="whole")
    parser.add_argument("--asr-backend", choices=["whisper", "qwen", "heart"], default="whisper")
    parser.add_argument("--lyrics-input", choices=["vocals", "source"], default="vocals")
    parser.add_argument(
        "--lyrics-alignment", choices=["native", "qwen", "whisper", "anchors"], default="native"
    )
    parser.add_argument("--lyrics-python", type=Path, help="Optional isolated lyric runtime Python")
    parser.add_argument(
        "--inference-python", type=Path, help="Optional isolated Next model runtime Python"
    )
    parser.add_argument(
        "--anchor-model", choices=["small", "large-v3-turbo", "dual"], default="small"
    )
    parser.add_argument(
        "--melody-decoder", choices=["classic", "stable", "rest"], default=Settings().melody_decoder
    )
    parser.add_argument(
        "--rhythm-backend",
        choices=["librosa", "librosa_percussive", "beat_this"],
        default=Settings().rhythm_backend,
    )
    parser.add_argument(
        "--rhythm-checkpoint",
        choices=["small0", "final0", "fold2", "fold3", "fold4", "fold6"],
        default="small0",
    )
    parser.add_argument(
        "--harmony-backend", choices=["stft", "cqt"], default=Settings().harmony_backend
    )
    parser.add_argument(
        "--mixture-consistency",
        action=argparse.BooleanOptionalAction,
        default=Settings().mixture_consistency,
    )


def get_settings(args) -> Settings:
    fields = Settings.model_fields
    return Settings(
        **{
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
            if key in fields
        }
    ).resolved()


def doctor() -> dict:
    from .pipeline import installed_versions

    result = {
        "python": sys.version,
        "executable": sys.executable,
        "model_dir": Settings().model_dir,
        "packages": installed_versions(
            [
                "music-workbench-local",
                "torch",
                "torchaudio",
                "demucs",
                "faster-whisper",
                "ctranslate2",
                "torchcrepe",
                "librosa",
                "av",
            ]
        ),
        "cuda_available": False,
    }
    if importlib.util.find_spec("torch"):
        try:
            import torch

            result["cuda_available"] = torch.cuda.is_available()
            result["torch_cuda_version"] = torch.version.cuda
            if torch.cuda.is_available():
                props = torch.cuda.get_device_properties(0)
                result["gpu"] = {"name": props.name, "memory_mb": props.total_memory // 1024**2}
        except (ImportError, OSError) as error:
            result["torch_error"] = str(error)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="music-studio",
        description="Local song analysis: stems, timed lyrics, MIDI, chords, beats.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Show runtime and GPU information")
    ui = commands.add_parser("ui", help="Open the local song-analysis workbench")
    add_settings(ui)
    ui.add_argument("--workspace", type=Path)
    ui.add_argument("--port", type=int, default=8920)
    ui.add_argument("--open", action="store_true", dest="open_browser")
    ui.add_argument("--interface", choices=["classic", "next", "create"], default="create")
    analysis = commands.add_parser("analyze", help="Analyze a song entirely on this computer")
    analysis.add_argument("input", type=Path)
    analysis.add_argument("--output", "-o", type=Path, required=True)
    analysis.add_argument(
        "--resume", action="store_true", help="Reuse only verified stage artifacts"
    )
    add_settings(analysis)
    analysis.add_argument("--language", help="Language code, e.g. zh/en; default: detect")
    analysis.add_argument("--pitch-backend", choices=["crepe", "pyin"], default="crepe")
    analysis.add_argument("--pitch-threshold", type=float, default=0.35)
    analysis.add_argument("--segment-seconds", type=float, default=6.0)
    model = commands.add_parser("models", help="Download models before working offline")
    actions = model.add_subparsers(dest="model_action", required=True)
    download = actions.add_parser("download")
    add_settings(download)
    validate = commands.add_parser(
        "validate", help="Check project schema, artifacts and audio lengths"
    )
    validate.add_argument("project", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps(doctor(), ensure_ascii=False, indent=2))
        elif args.command == "ui":
            try:
                from .ui.server import serve
            except ImportError:
                raise RuntimeError(
                    "Install the UI dependencies: pip install -e '.[ui,inference]'"
                ) from None
            workspace = args.workspace or Path(
                {"next": "outputs/next", "create": "outputs/create"}.get(
                    args.interface, "outputs/ui"
                )
            )
            serve(workspace, get_settings(args), args.port, args.open_browser, args.interface)
        elif args.command == "models":
            from .pipeline import run_worker

            settings = get_settings(args)
            with tempfile.TemporaryDirectory(prefix="music-studio-models-") as temporary:
                root = Path(temporary)
                result = run_worker(
                    {
                        "stage": "download",
                        "settings": settings.model_dump(),
                        "output": str(root),
                        "result": str(root / "models.json"),
                    },
                    root / "download.log",
                )
                print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "validate":
            from .validation import validate_project

            report = validate_project(args.project)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            from .pipeline import analyze

            analyze(args.input, args.output, get_settings(args), resume=args.resume)
    except KeyboardInterrupt:
        print("Cancelled. Completed stages are cached; rerun with --resume.", file=sys.stderr)
        raise SystemExit(130) from None
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
