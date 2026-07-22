from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sprite_pipeline.config import load_config
from sprite_pipeline.pipeline import SpritePipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Hybrid pixel-art generation and review pipeline")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("tools/sprite_pipeline/configs/human_warrior_m01.json"),
        help="Path to the character pipeline manifest",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root used to resolve reference paths",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Generate, filter and rank candidates")
    run_parser.add_argument("--frame-id", required=True)
    run_parser.add_argument("--output-root", type=Path, default=Path("art_pipeline_runs"))
    run_parser.add_argument("--candidates", type=int)
    run_parser.add_argument("--top-k", type=int)
    run_parser.add_argument("--max-rounds", type=int)
    run_parser.add_argument("--extra-reference")

    validate_parser = subparsers.add_parser("validate", help="Run deterministic technical checks only")
    validate_parser.add_argument("--frame-id", required=True)
    validate_parser.add_argument("--input-dir", type=Path, required=True)
    validate_parser.add_argument("--output-root", type=Path, default=Path("art_pipeline_runs"))

    args = parser.parse_args()
    try:
        config = load_config(args.manifest, args.repo_root)
        pipeline = SpritePipeline(config)
        if args.command == "run":
            run_dir = pipeline.run(
                frame_id=args.frame_id,
                output_root=args.output_root,
                candidates=args.candidates,
                top_k=args.top_k,
                max_rounds=args.max_rounds,
                extra_reference=args.extra_reference,
            )
        else:
            run_dir = pipeline.validate_directory(
                frame_id=args.frame_id,
                input_dir=args.input_dir,
                output_root=args.output_root,
            )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
