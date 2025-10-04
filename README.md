# Directory Tree Maker

  A cross-platform Python tool to generate visual tree views of project folders.  
  The script prints the tree to the terminal **and** saves it to timestamped text files.

---
  ## 1. Features
  - Works on **Windows**, **macOS**, and **Linux**.
  - Timestamped output files:  
    `[root_folder_name-YYYY.MM.DD.HH.MM.SS].txt`
  - Saved by default in:
    - `root_folder/.trees/`
    - `directory-tree-maker/.trees/[root_folder_name]/`
  - Additional save directories can be configured.
  - Skips or limits traversal into heavy folders (`node_modules`, `.git`, etc.).
  - Configurable depth limit, hidden file policy, and inclusion/exclusion patterns.
  - Uses only the Python standard library.

---
  ## 2. Requirements
  - Python 3.8 or higher

---
  ## 3. Setup

  ### Clone the repo
  ```bash
  git clone https://github.com/LouieMorais/directory-tree-maker.git
  cd directory-tree-maker
````

  ### (Optional) Create a virtual environment

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate   # macOS/Linux
  # or
  .\.venv\Scripts\Activate.ps1   # Windows PowerShell
  ```

----

  ## 4. Usage

  1. Open `directory-tree-maker.py` and configure the **USER CONFIGURATION** block at the top:
     - `root_folder` = path to the project you want to scan.
     - `only_dirs`, `show_hidden`, `max_depth`, and pattern lists as needed.
     - Optional: add custom save directories in `extra_save_dirs`.
  2. Run the script:

  **Windows (PowerShell)**

  ```powershell
  py .\directory-tree-maker.py
  ```

  **macOS/Linux**

  ```bash
  python3 ./directory-tree-maker.py
  ```

  1. Output:
     - Tree is printed in the terminal.
     - A timestamped `.txt` file is saved in the configured destinations.

----

  ## 5. Example

  ```
  housarmony/
  ├── app/
  │   ├── index.tsx
  │   └── tasks/
  │       ├── item.tsx
  │       └── list.tsx
  ├── assets/
  │   ├── fonts/
  │   └── img/
  └── utils/
      ├── assignPoints.ts
      └── sortTasks.ts
  ```

  Saved to:

  ```
  housarmony/.trees/housarmony-2025.10.04.16.45.12.txt
  directory-tree-maker/.trees/housarmony/housarmony-2025.10.04.16.45.12.txt
  ```

----

  ## 6. License

  ```
  Apache License
  Version 2.0, January 2004
  http://www.apache.org/licenses/
  
  TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
  
  Copyright 2025 Louie Morais
  
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at
  
     http://www.apache.org/licenses/LICENSE-2.0
  
  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
  ```

  
