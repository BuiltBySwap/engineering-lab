# How to run the code

Every code cell in this book is meant to run. There are three ways to run it, and one automatic check that proves it.

![Check notebooks](https://github.com/BuiltBySwap/engineering-lab/actions/workflows/check.yml/badge.svg)

| Where | Setup | Good for |
|---|---|---|
| **Colab** | None: click **Open in Colab** at the top of a notebook | Python cells, nothing to install. Kotlin cells need the setup cell first (about a minute, once per session) |
| **VS Code on your computer** | `bash tools/setup_local.sh` (once) | Everything, and the fastest. Edit and run in the same place |
| **GitHub check** | Automatic on every push | Proves every cell runs, including the ones that download libraries. Green tick = it runs |

## VS Code (recommended)

1. `bash tools/setup_local.sh` creates the Python environment, installs the packages and registers the notebook kernel.
2. Open the repo folder in VS Code and open a notebook from `docs/topics/`.
3. Click **Select Kernel** (top right) and choose **Engineering Lab (.venv)**.
4. Run cells with **Shift + Enter**. For Kotlin, run the notebook's setup cell first, then any `%%kotlin` cell.

## Check that everything runs

```bash
bash tools/check.sh             # builds the site strictly, then runs every code cell
bash tools/check.sh --online    # also the cells that download libraries
```

| Symbol | Meaning |
|---|---|
| ✅ | the cell ran |
| ❌ | the cell failed: the last lines of the error are shown |
| ⏭ | skipped on purpose (setup cells, or cells that need `--online`) |
| ✏️ | an exercise that is not solved yet (this is expected until you solve it) |

## What each kind of cell needs

| Cell | Needs |
|---|---|
| Python | `numpy` and `matplotlib` (installed by the setup script) |
| `%%kotlin` | Java 17 or newer, and internet the first time (the Kotlin compiler is about 80 MB) |
| `%%kotlin` with `@file:DependsOn` | Internet, to download that library |
| A Ktor server on a port | Run it from `kaizen/server-ktor`. A notebook uses Ktor's in-process test host instead |

## If a cell fails

1. Read the last line of the error. A missing package prints `pip install ...`.
2. Kotlin cells do not share state: put the function and its checks in the same cell.
3. Still stuck: send the notebook name, the cell number and the last 5 lines of the error.
