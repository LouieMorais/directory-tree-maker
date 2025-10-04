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
```

### (Optional) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# or
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
```

---

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

---

## 5. Examples

### Example 1

**Settings**

- Limiting directory depth to 3 levels, including root
- Listing directories and files
- Showing hidden and excluded entries but not going beyond level 1
- Note that script will warn which directories have been 

```
housetasker/
├── .expo/
├── .git/
├── .husky/
├── .manuals/
├── .trees/
├── .vscode/
├── __tests__/
├── android/
│   ├── .gradle/
│   ├── .kotlin/
│   ├── app/
│   │   ├── .cxx/
│   │   ├── build/
│   │   ├── src/
│   │   ├── build.gradle
│   │   ├── debug.keystore
│   │   └── proguard-rules.pro
│   ├── build/
│   │   ├── generated/
│   │   └── reports/
│   ├── gradle/
│   │   └── wrapper/
│   ├── .gitignore
│   ├── build.gradle
│   ├── gradle.properties
│   ├── gradlew
│   ├── gradlew.bat
│   └── settings.gradle
├── db/
│   ├── .archive/
│   ├── .db backups/
│   ├── housetasker_db_create.sql
│   ├── housetasker_db_schema.sql
│   ├── housetasker_db_seed_final.sql
│   └── tasks_seed_data.csv
├── node_modules/
├── src/
│   ├── app/
│   │   ├── tasks/
│   │   ├── CongratsScreen.tsx
│   │   ├── DevSupabaseTestScreen.tsx
│   │   └── SplashScreen.tsx
│   ├── assets/
│   │   ├── fonts/
│   │   ├── img/
│   │   ├── adaptive-icon.png
│   │   ├── favicon.png
│   │   ├── icon.png
│   │   └── splash-icon.png
│   ├── components/
│   │   ├── FilterDropdown.tsx
│   │   └── TaskCard.tsx
│   ├── hooks/
│   │   └── useTasks.ts
│   ├── services/
│   │   ├── supabaseClient.ts
│   │   └── taskService.ts
│   ├── types/
│   │   ├── housemate.ts
│   │   ├── navigation.ts
│   │   └── task.ts
│   ├── utils/
│   │   └── sortTasks.ts
│   └── theme.ts
├── supabase/
│   ├── .temp/
│   ├── functions/
│   │   └── reseed_demo_data/
│   ├── .gitignore
│   └── config.toml
├── .env.test
├── .gitattributes
├── .gitignore
├── .prettierignore
├── .prettierrc.cjs
├── app.config.js
├── App.tsx
├── babel.config.js
├── eslint.config.cjs
├── index.ts
├── package-lock.json
├── package.json
├── README.md
└── tsconfig.json
```

Saved to:

```
housarmony/.trees/housarmony-2025.10.04.16.45.12.txt
directory-tree-maker/.trees/housarmony/housarmony-2025.10.04.16.45.12.txt
```


### Example 2

**Settings**

- No limit of directory depth
- Listing directories only (no files)
- Hiding hidden and excluded entries
- Exclusions as per .gitignore (manually copied to script configuration header)

Saved to:

```
housarmony/.trees/housarmony-2025.10.04.16.45.12.txt
directory-tree-maker/.trees/housarmony/housarmony-2025.10.04.16.45.12.txt
```

---

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
