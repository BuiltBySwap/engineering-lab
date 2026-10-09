"""Run Kotlin in a notebook: put %%kotlin on the first line of a cell.

Setup (once per Colab session), as the first code cell of a notebook:

    !curl -sL -o kotlin_magic.py https://raw.githubusercontent.com/BuiltBySwap/engineering-lab/main/tools/kotlin_magic.py
    %run kotlin_magic.py

How it works
- The first run downloads the Kotlin compiler (about 80 MB) and, if needed, a JDK. Later runs are faster.
- Each %%kotlin cell is a Kotlin SCRIPT: top-level statements run directly, no main() needed.
- Cells do not share state: put the function and its checks in the same cell.
- kotlin.test is on the classpath, so assertEquals(...) works for DSA checks.
- Libraries: add @file:DependsOn("group:artifact:version") at the top of the cell (needs internet).
- Options: %%kotlin --timeout 600
"""
import os
import pathlib
import re
import subprocess
import tempfile
import time
import urllib.request
import zipfile

KOTLIN_VERSION = "2.2.10"
MIN_JAVA = 17
HOME = pathlib.Path(os.environ.get("KOTLINC_HOME", pathlib.Path.home() / ".kotlinc"))
ZIP_URL = f"https://github.com/JetBrains/kotlin/releases/download/v{KOTLIN_VERSION}/kotlin-compiler-{KOTLIN_VERSION}.zip"


def _java_major() -> int:
    try:
        out = subprocess.run(["java", "-version"], capture_output=True, text=True).stderr
    except FileNotFoundError:
        return 0
    match = re.search(r'version "(\d+)(?:\.(\d+))?', out)
    if not match:
        return 0
    major = int(match.group(1))
    return int(match.group(2) or 0) if major == 1 else major  # "1.8.0" means Java 8


def _ensure_java() -> None:
    if _java_major() >= MIN_JAVA:
        return
    print("Installing a JDK (one time, about a minute)...")
    result = subprocess.run("apt-get -qq update && apt-get -qq install -y openjdk-21-jdk-headless",
                            shell=True, capture_output=True, text=True)
    if _java_major() < MIN_JAVA:
        raise RuntimeError(
            f"Kotlin needs JDK {MIN_JAVA}+ and the automatic install failed.\n"
            f"Install a JDK and run this cell again.\n{result.stderr[-400:]}"
        )


def _ensure_kotlinc() -> pathlib.Path:
    root = HOME / KOTLIN_VERSION
    exe = root / "kotlinc" / "bin" / "kotlinc"
    if exe.exists():
        return exe
    root.mkdir(parents=True, exist_ok=True)
    print(f"Downloading the Kotlin {KOTLIN_VERSION} compiler (one time, about 80 MB)...")
    archive = root / "kotlinc.zip"
    urllib.request.urlretrieve(ZIP_URL, archive)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(root)
    archive.unlink()
    for tool in (root / "kotlinc" / "bin").iterdir():
        tool.chmod(0o755)
    return exe


def _tidy(errors: str) -> str:
    """Show the error and the line in YOUR cell; hide library stack frames and temp paths."""
    errors = re.sub(r"[^\s:(]*cell\.main\.kts", "cell", errors)
    kept = [ln for ln in errors.splitlines() if not re.match(r"\s+at (kotlin|java|jdk|org\.jetbrains)\.", ln)]
    return "\n".join(kept) + ("\n" if kept else "")


def run_kotlin(code: str, timeout: int = 300) -> int:
    """Compile and run a Kotlin script. Prints its output. Returns the exit code."""
    _ensure_java()
    kotlinc = _ensure_kotlinc()
    test_jar = kotlinc.parent.parent / "lib" / "kotlin-test.jar"
    with tempfile.TemporaryDirectory() as tmp:
        script = pathlib.Path(tmp) / "cell.main.kts"
        script.write_text(code, encoding="utf-8")
        cmd = [str(kotlinc)]
        if test_jar.exists():
            cmd += ["-cp", str(test_jar)]
        cmd += ["-script", str(script)]
        started = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"Stopped: the cell ran longer than {timeout} s (use %%kotlin --timeout N to allow more).")
            return 124
        output = result.stdout
        errors = _tidy(result.stderr)
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    if errors:
        print(errors, end="" if errors.endswith("\n") else "\n")
    print(f"[kotlin finished in {time.time() - started:.1f} s, exit code {result.returncode}]")
    return result.returncode


def _kotlin_cell(line: str, cell: str) -> None:
    match = re.search(r"--timeout\s+(\d+)", line or "")
    run_kotlin(cell, int(match.group(1)) if match else 300)


try:
    from IPython.core.magic import register_cell_magic

    register_cell_magic("kotlin")(_kotlin_cell)
    print(f"%%kotlin is ready (Kotlin {KOTLIN_VERSION}). The first Kotlin cell downloads the compiler.")
except ImportError:
    print("IPython not found: call run_kotlin(code) directly.")
