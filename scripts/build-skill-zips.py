#!/usr/bin/env python3

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def iter_skill_dirs() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def iter_files(skill_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in skill_dir.rglob("*")
        if path.is_file() and path.name != ".DS_Store" and path.suffix != ".zip"
    )


def build_skill_zip(skill_dir: Path) -> Path:
    output_path = SKILLS_DIR / f"{skill_dir.name}.zip"

    with tempfile.NamedTemporaryFile(
        dir=SKILLS_DIR, prefix=f"{skill_dir.name}.", suffix=".zip", delete=False
    ) as tmp_file:
        temp_path = Path(tmp_file.name)

    try:
        with ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as zip_file:
            for file_path in iter_files(skill_dir):
                archive_path = file_path.relative_to(SKILLS_DIR)
                zip_file.write(file_path, archive_path)

        shutil.move(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return output_path


def main() -> int:
    if not SKILLS_DIR.exists():
        raise SystemExit(f"Missing skills directory: {SKILLS_DIR}")

    for skill_dir in iter_skill_dirs():
        output_path = build_skill_zip(skill_dir)
        print(f"Built {output_path.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
