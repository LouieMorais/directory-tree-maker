# Setup and usage: `directory-tree-maker`

## 1. Prerequisites

- Python **3.8+** installed.
- A terminal:
  - **Windows:** PowerShell.
  - **macOS/Linux:** Terminal.

Verify Python:

- **Windows (PowerShell)**

```powershell
py --version
```

- **macOS/Linux**

```bash
python3 --version
```

---

## 2. Create the project directory

- **Windows (PowerShell)**

```powershell
cd ~
mkdir directory-tree-maker
cd directory-tree-maker
```

- **macOS/Linux**

```bash
cd ~
mkdir -p directory-tree-maker
cd directory-tree-maker
```

---

## 3. (Optional) Create and activate a virtual environment

- **Windows (PowerShell)**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- **macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Confirm activation: the prompt should start with `(.venv)`.

---

## 4. Create the script file `directory-tree-maker.py`

- **Windows (PowerShell)**

```powershell
notepad .\directory-tree-maker.py
```

- **macOS/Linux**

```bash
nano directory-tree-maker.py
```

Paste your final Python code into this file and save.

---

## 5. Configure the script (USER CONFIGURATION block)

Open `directory-tree-maker.py` and set the configuration at the top:

- **Target folder (`root_folder`)**
  Windows example:

  ```python
  root_folder = Path(r"D:\Projects\housarmony").resolve()
  ```

  macOS example:

  ```python
  root_folder = Path("/Users/louie/Projects/housarmony").resolve()
  ```

  Linux example:

  ```python
  root_folder = Path("/home/louie/Projects/housarmony").resolve()
  ```

- **Common toggles**

  ```python
  only_dirs = False        # True to show directories only
  show_hidden = False      # True to include hidden (dot) entries
  max_depth = None         # e.g., 2 to limit depth, None for no limit
  ```

- **Patterns (glob semantics; matched against basename and POSIX relative path)**

  ```python
  exclude_patterns = ["*.log", "**/dist/**", "**/build/**"]
  non_recursive_patterns = [".git", "node_modules", "__pycache__", ".venv", ".idea", ".DS_Store"]
  # Optional hidden policy when show_hidden = True:
  # hidden_non_recursive_patterns = [".*", "**/.cache/**"]
  # hidden_recursive_exceptions = [".vscode", "**/.config/**"]
  ```

---

## 6. Run the script

- **Windows (PowerShell)**

```powershell
py .\directory-tree-maker.py
```

- **macOS/Linux**

```bash
python3 ./directory-tree-maker.py
```

What happens:

- The directory tree is printed to the terminal.
- A text file named **`[root_folder.name].txt`** is created in the **current working directory** (the `directory-tree-maker` folder).
  Example: if `root_folder` is `/Users/louie/Projects/housarmony`, the output file will be `housarmony.txt` in `~/directory-tree-maker`.

---

## 7. View the generated text file

- **Windows**

```powershell
notepad .\housarmony.txt
```

- **macOS**

```bash
open ./housarmony.txt
```

- **Linux**

```bash
xdg-open ./housarmony.txt
```

---

## 8. Ensure Unicode box-drawing renders correctly

If the connectors (`├──`, `└──`, `│`) look incorrect:

- **Windows (PowerShell)**

```powershell
chcp 65001
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
```

Use a UTF-8 capable font in Windows Terminal (e.g., Cascadia Mono).

- **macOS/Linux**
  Terminals are UTF-8 by default; ensure your font supports box-drawing characters.

---

## 9. Common configurations

- **Quick architectural overview (directories only, shallow depth)**

  ```python
  only_dirs = True
  max_depth = 2
  ```

- **Show heavy folders but do not expand them**

  ```python
  non_recursive_patterns = [".git", "node_modules", "__pycache__", ".venv", ".idea", ".DS_Store", "**/vendor/**"]
  ```

- **Exclude generated artefacts entirely**

  ```python
  exclude_patterns = ["**/dist/**", "**/coverage/**", "*.map", "*.min.*"]
  ```

- **Include hidden config folders selectively**

  ```python
  show_hidden = True
  hidden_non_recursive_patterns = [".*", "**/.cache/**"]
  hidden_recursive_exceptions = [".vscode", "**/.config/**"]
  ```

---

## 10. Re-run against a different project

Edit `root_folder` in `directory-tree-maker.py`, then run the same command again:

- **Windows (PowerShell)**

```powershell
py .\directory-tree-maker.py
```

- **macOS/Linux**

```bash
python3 ./directory-tree-maker.py
```

A new `[targetname].txt` is generated in `directory-tree-maker`.

---

## 11. Deactivate the virtual environment (if used)

- **Windows (PowerShell)**

```powershell
deactivate
```

- **macOS/Linux**

```bash
deactivate
```

---

## 12. Troubleshooting

- **“Permission denied” entries**
  The script annotates them (`⟨permission denied⟩`) and continues.
- **No output file appears**
  Ensure you are running from inside `directory-tree-maker` and have write permissions. The file is written to the **current working directory**, not inside `root_folder`.
- **Hidden items not shown**
  Set `show_hidden = True`. If `hidden_include_patterns` is non-empty, only hidden entries matching those patterns are included.
- **Excessive output**
  Set `max_depth` to a small integer, add more `non_recursive_patterns`, or temporarily enable `non_recursive_catch_all = True`.
