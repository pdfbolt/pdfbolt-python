from __future__ import annotations

import glob
import os
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
REQUIRED_WHEEL_FILES = {
    "pdfbolt/__init__.py",
    "pdfbolt/types.py",
    "pdfbolt/py.typed",
    f"pdfbolt-{VERSION}.dist-info/METADATA",
    f"pdfbolt-{VERSION}.dist-info/WHEEL",
    f"pdfbolt-{VERSION}.dist-info/RECORD",
}
FORBIDDEN_WHEEL_PREFIXES = ("tests/", "examples/", "scripts/")
FORBIDDEN_SDIST_PREFIXES = (".git/", ".venv/", "build/", "dist/")


def main() -> None:
    wheel = exactly_one(DIST / "*.whl")
    sdist = exactly_one(DIST / "*.tar.gz")

    check_wheel_contents(wheel)
    check_sdist_contents(sdist)
    check_installed_wheel(wheel)

    print(f"Packed package {wheel.name} passed wheel, sdist, and import smoke checks.")


def exactly_one(pattern: Path) -> Path:
    matches = [Path(match) for match in glob.glob(str(pattern))]
    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one match for {pattern}, found {len(matches)}.")
    return matches[0]


def check_wheel_contents(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    missing = sorted(REQUIRED_WHEEL_FILES - names)
    if missing:
        raise SystemExit(f"Wheel is missing required files: {', '.join(missing)}")

    forbidden = [
        name for name in names if name == ".env" or name.startswith(FORBIDDEN_WHEEL_PREFIXES)
    ]
    if forbidden:
        raise SystemExit(f"Wheel should not include: {', '.join(sorted(forbidden))}")


def check_sdist_contents(sdist: Path) -> None:
    with tarfile.open(sdist) as archive:
        names = {strip_sdist_root(member.name) for member in archive.getmembers()}

    required = {
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "src/pdfbolt/__init__.py",
        "src/pdfbolt/types.py",
        "src/pdfbolt/py.typed",
        "tests/test_client.py",
        "tests/typecheck_usage.py",
    }
    missing = sorted(required - names)
    if missing:
        raise SystemExit(f"Sdist is missing required files: {', '.join(missing)}")

    forbidden = [name for name in names if name.startswith(FORBIDDEN_SDIST_PREFIXES)]
    if forbidden:
        raise SystemExit(f"Sdist should not include: {', '.join(sorted(forbidden))}")


def check_installed_wheel(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="pdfbolt-python-pack-") as temp_dir:
        target = Path(temp_dir) / "site"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--target",
                str(target),
                str(wheel),
            ],
            check=True,
        )

        code = (
            "import pdfbolt; "
            "required = ['PDFBolt', 'DirectConversionResult', 'VERSION', "
            "'DirectConvertParams', 'SyncConvertParams', 'AsyncConvertParams']; "
            "missing = [name for name in required if not hasattr(pdfbolt, name)]; "
            "assert not missing, f'missing exports: {missing}'"
        )
        subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            env={**os.environ, "PYTHONPATH": str(target)},
        )


def strip_sdist_root(name: str) -> str:
    parts = name.split("/", 1)
    return parts[1] if len(parts) == 2 else name


if __name__ == "__main__":
    main()
