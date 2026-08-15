from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import heart_anatomy_v02 as anatomy_v02
import heart_anatomy_v02_assembly_fix as assembly_fix
import heart_anatomy_v03_unified_shell as visible_v03

_original_upgrade = anatomy_v02.upgrade


def _upgrade_reassemble_and_replace_visible_shell(build):
    build = _original_upgrade(build)
    build = assembly_fix.apply(build)
    return visible_v03.apply(build)


anatomy_v02.upgrade = _upgrade_reassemble_and_replace_visible_shell

import heart_starling_anrep_v02_runner as runner  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(runner.app.main())
