#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
directory-tree-maker.py
- Generates an ASCII tree for a directory.
- Adds reports per Louie’s final spec:
  • Depth-Pruned Directories (global max_depth only), with total depth and skipped levels.
  • Rule-Excluded Folders (hidden, gitignore list, exclusion list, override -1).
  • “Skipped Total: X Folders | Y Files” at the bottom of each section.
- Two-tab spacing between columns (~16 spaces).
- Path compression for long paths: '/...(<n>)/' between first 3 and last 2 segments.
- Dual save locations + optional extras.
- Standard library only. No symlink following.
- Live progress: shows “Starting …”, “Calculating directory: …”, and “Finished … ✔”.
"""

from __future__ import annotations

import os
import sys
import fnmatch
import time
from collections import deque
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple

# ======================================
# USER CONFIGURATION – EDIT THIS SECTION
# ======================================

# Later configurations supersede earlier ones.

# -----------------------------------------------------------------
# 0. How to Write Patterns
#
# Patterns use the same wildcards as the Windows command line and
# macOS/Linux shells (called glob patterns).
#
# Pattern          | Matches
# -----------------|---------------------------------------------
# "*.log"          | All files ending in .log
# "*/temp/*"       | Any folder path containing "temp"
# "node_modules"   | A folder exactly named "node_modules"
# ".*"             | All hidden files and folders
# "docs/*.md"      | Markdown files in the "docs" folder
# -----------------------------------------------------------------

# --------------------------------------
# 1. Path and Directory Settings
# --------------------------------------

# 1.1. Path to Directory
# Path to the folder you want to crawl and list as a tree.
# For Windows: "C:/dev/project_folder"
# For macOS/Linux: "/Users/yourname/Dropbox/.dev/housetasker"
root_folder = r"D:\Users\Louie Morais\Dropbox\.dev\housetasker"

# 1.2. Maximum Depth to Traverse (Crawl)
# Controls how many directory levels are crawled and displayed.
# Depth Values:
#   0 = all levels (no limit)
#   1 = root only
#   2 = root and its immediate children
#   3+ = crawl that many levels deep
# Notes:
# - 0 behaves the same as "no limit"
# - Negative values are not accepted
max_depth = 3

# 1.3. Show Only Directories or Include Files
# Controls whether files are displayed alongside folders in the tree.
# If True  = show only folder names (no files)
# If False = show both folders and files
only_dirs = False

# 1.4. Case-Sensitive Sorting
# Controls how names are alphabetically sorted.
# If True  = case-sensitive sort (A–Z then a–z, e.g., B.txt, a.txt, c.TXT)
# If False = case-insensitive sort (alphabetical regardless of case,
#                                   e.g., a.txt, B.txt, c.TXT)
case_sensitive_sort = False

# 1.5. Directory and File Listing Order
# Controls the order in which directories and files are listed.
# If True  = directories appear before files (like Windows Explorer)
# If False = directories and files are listed together alphabetically
#            (like macOS Finder or the "ls" command)
list_dirs_first = True

# -----------------------------------------
# 2. Tree Listing Exceptions and Exclusions
# -----------------------------------------

# 2.1. Use .gitignore in Project Folder
# If True  = the script reads the ".gitignore" file in the root folder
#            and applies its exclusion rules.
# If False = ".gitignore" is ignored.
use_gitignore = True

# 2.2. Hidden Files and Folders (those starting with ".")
# If True  = show hidden files and folders.
#            Hidden entries follow the same depth and inclusion rules
#            as normal entries, and are not affected by ".gitignore".
# If False = hidden entries are excluded from the tree.
show_hidden = False

# 2.3. Exclude Specific Folders and Files
# Patterns listed here will always be excluded from the tree.
# This setting adds to the list of exclusions in ".gitignore" (if set to true).
# Refer to Section 0 for pattern examples.
# Usage: exclude_patterns = [".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".DS_Store",]
exclude_patterns = []

# 2.4. File, Folder, and Depth Overrides
# Define custom depth or inclusion/exclusion rules for specific entries.
# These overrides take precedence over all other settings.
#
# Each entry is a pair: ("pattern", depth)
# Depth values:
#   -1 = exclude this entry entirely
#    0 = unlimited depth for this entry
#    1+ = crawl this many levels under the entry
#
# Example:
# settings_override = [
#     ("docs", 2),             # crawl "docs" folder to depth 2
#     ("src", -1),             # exclude "src" entirely
#     ("*.txt", 0),            # show all .txt files without depth limit
# ]
#
# Refer to Section 0 for valid pattern formats.
settings_override = []

# --------------------------------------
# 3. Reporting Settings
# --------------------------------------

# 3.1. Generate Summary Reports
# Controls whether summary reports are added after the tree output.
# If True  = include post-tree sections:
#              - Depth-Pruned Directories
#              - Rule-Excluded Directories
#              - Excluded Files Summary
# If False = output the tree only (no reports)
show_reports = True

# 3.2. Report Save Locations
# By default, each report is saved in two locations:
#   1. Inside the project folder:
#      [root_folder]/.trees/[root_name-yyyy.mm.dd.hh.mm.ss].txt
#   2. Inside the script folder:
#      directory-tree-maker/.trees/[root_name]/[root_name-yyyy.mm.dd.hh.mm.ss].txt
#
# You can specify extra save folders here (absolute paths as strings).
# Invalid paths are ignored, and the file is still saved to the defaults.
# Usage: extra_save_dirs = ["D:/Backups/trees", "/Users/louie/trees"]
extra_save_dirs = []

# 3.3. Recursion Protection (Depth Scan Limit)
# Limits how deep the script measures skipped directories when reporting
# depth-pruned folders.
#
# Depth Values:
#   0 = no limit (scan fully)
#   1–999 = measure up to this many additional levels
#
# Example:
#   25 (default) means measure up to 25 levels beyond the cutoff.
# Negative values are not accepted.
max_depth_measure_limit = 25

# ======================================
# END OF CONFIGURATION SECTION
# ======================================


# ---------------------- Internal helpers & engine ----------------------

_VERBOSE = True  # Set to False to silence progress messages

_TWO_TABS = " " * 16  # Two-tab spacing between columns

def _log(msg: str) -> None:
    if _VERBOSE:
        print(msg)

def print_progress(stage: str, current_dir: str | None = None, done: bool = False):
    """Dynamic one-line progress update for heavy loops."""
    if not _VERBOSE:
        return
    if done:
        sys.stdout.write(f"\r-> Finished {stage} calculations ✔{' ' * 40}\n")
        sys.stdout.flush()
        return
    if current_dir:
        sys.stdout.write(f"\r-> Calculating directory: {current_dir[:70]:<70}")
    else:
        sys.stdout.write(f"\r-> Starting {stage} calculations ...")
    sys.stdout.flush()

def _normalise_root_folder(path_str: str) -> Path:
    """Normalises separators, expands ~, resolves absolute path, warns if missing."""
    try:
        s = os.path.expanduser(path_str)
        s = s.replace("\\", "/")
        p = Path(s).resolve()
    except Exception:
        p = Path(path_str).resolve()
    if not p.exists():
        print(f"Warning: The path '{p}' does not exist.", file=sys.stderr)
    return p

def _sort_key(name: str) -> str:
    return name if case_sensitive_sort else name.lower()

def _is_hidden(p: Path) -> bool:
    if p.name.startswith("."):
        return True
    if os.name == "nt":
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
            return attrs != -1 and bool(attrs & 2)
        except Exception:
            return False
    return False

def _to_posix_rel(p: Path, root: Path) -> str:
    try:
        rel = p.relative_to(root)
        s = rel.as_posix()
        return "" if s == "." else s
    except Exception:
        s = os.path.relpath(str(p), str(root)).replace(os.sep, "/")
        return "" if s == "." else s

def _matches_any(name: str, rel: str, patterns: Iterable[str], is_dir: bool) -> bool:
    n = name if case_sensitive_sort else name.lower()
    r = rel if case_sensitive_sort else rel.lower()
    for pat in patterns or []:
        p = pat if case_sensitive_sort else pat.lower()
        if fnmatch.fnmatchcase(n, p) or fnmatch.fnmatchcase(r, p) or (is_dir and fnmatch.fnmatchcase(r + "/", p)):
            return True
    return False

def _read_gitignore(root: Path) -> List[str]:
    if not use_gitignore:
        return []
    gi = root / ".gitignore"
    if not gi.exists():
        return []
    pats: List[str] = []
    try:
        for line in gi.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.endswith("/"):
                s = s[:-1]
            pats.append(s)
    except Exception:
        pass
    return pats

class Override:
    __slots__ = ("pattern", "depth")
    def __init__(self, pattern: str, depth: int):
        self.pattern = pattern
        self.depth = depth

def _compile_overrides(entries: List[Tuple[str, int]]) -> List[Override]:
    out: List[Override] = []
    for pair in entries:
        try:
            pat, dep = pair
            if not isinstance(pat, str):
                continue
            if not isinstance(dep, int):
                continue
            out.append(Override(pat, dep))
        except Exception:
            continue
    return out

def _compress_path(rel_with_slash: str) -> str:
    """Compress long paths using '/...(n)/' between the first 3 and last 2 segments."""
    rel = rel_with_slash.rstrip("/")
    if not rel:
        return "./"
    parts = rel.split("/")
    if len(parts) <= 5:
        return rel + "/"
    omitted = len(parts) - 5
    return "/".join(parts[:3]) + f"/...({omitted}).../" + "/".join(parts[-2:]) + "/"

def _fmt_int(n: int) -> str:
    return f"{n:,}"

def _depth_limit_value_for_reports() -> Optional[int]:
    """Return None=unlimited; otherwise an integer extra levels to measure."""
    if max_depth_measure_limit is None:
        return None
    if isinstance(max_depth_measure_limit, int):
        if max_depth_measure_limit < 0:
            return 25
        if max_depth_measure_limit == 0:
            return None
        return max_depth_measure_limit
    return 25

def _effective_global_remaining(depth_from_root: int) -> Optional[int]:
    """Remaining levels allowed below current node by global max_depth (None = unlimited)."""
    if max_depth is None or max_depth == 0:
        return None
    if max_depth < 0:
        return None
    return max_depth - depth_from_root

def _remaining_from_override(ov_depth: int) -> Optional[int]:
    """Remaining levels allowed under an override start (None = unlimited)."""
    if ov_depth < 0:
        return 0
    if ov_depth == 0:
        return None
    return ov_depth

_OVERRIDES = _compile_overrides(settings_override)

# Root is resolved in main() after normalisation
ROOT: Optional[Path] = None
_GITIGNORE: List[str] = []
_EXCLUDES: List[str] = []

def _override_for(path: Path, rel: str, is_dir: bool) -> Optional[int]:
    """Return override depth for this entry, or None if none matches. -1 means exclude."""
    name = path.name
    for ov in _OVERRIDES:
        if _matches_any(name, rel, [ov.pattern], is_dir):
            return ov.depth
    return None

def _is_visible(path: Path, rel: str) -> bool:
    """Visibility decision. show_hidden overrides .gitignore for hidden entries."""
    hidden = _is_hidden(path)
    if hidden and not show_hidden:
        return False
    # If hidden and show_hidden=True → do not apply .gitignore patterns to hidden entries
    if not (hidden and show_hidden):
        if _matches_any(path.name, rel, _EXCLUDES, path.is_dir()):
            # may be resurrected by an override with depth>=0
            ov = _override_for(path, rel, path.is_dir())
            if ov is not None and ov >= 0:
                return True
            return False
    # settings_override -1 excludes even if visible so far
    ov = _override_for(path, rel, path.is_dir())
    if ov == -1:
        return False
    return True

def _iter_entries(dir_path: Path) -> List[Path]:
    try:
        entries = list(dir_path.iterdir())
    except Exception:
        return []
    if list_dirs_first:
        dirs = [p for p in entries if p.is_dir() and not p.is_symlink()]
        others = [p for p in entries if not (p.is_dir() and not p.is_symlink())]
        dirs.sort(key=lambda p: _sort_key(p.name))
        others.sort(key=lambda p: _sort_key(p.name))
        return dirs + others
    entries.sort(key=lambda p: _sort_key(p.name))
    return entries

def _scan_stats(start: Path, extra_limit: Optional[int]) -> Tuple[int, int, int]:
    """
    BFS scan under 'start' (not counting 'start' as a folder), respecting visibility.
    Returns (max_relative_depth, folders_count, files_count).
    extra_limit:
      None → unlimited extra depth
      k>=0 → measure at most k levels below 'start'
    """
    max_rel_depth = 0
    folders = 0
    files = 0
    dq = deque([(start, 0)])
    while dq:
        node, d = dq.popleft()
        if extra_limit is not None and d > extra_limit:
            continue
        try:
            for e in node.iterdir():
                rel = _to_posix_rel(e, ROOT)  # type: ignore[arg-type]
                if not _is_visible(e, rel):
                    continue
                if e.is_dir() and not e.is_symlink():
                    folders += 1
                    nd = d + 1
                    max_rel_depth = max(max_rel_depth, nd)
                    dq.append((e, nd))
                elif e.is_file():
                    files += 1
        except Exception:
            continue
    return max_rel_depth, folders, files

class Reports:
    def __init__(self) -> None:
        # Filled after the “compute stats” phase (before printing the tree)
        # relpath/ -> (total_depth_abs, skipped_levels, skipped_folders, skipped_files)
        self.depth_pruned: Dict[str, Tuple[int, int, int, int]] = {}
        # relpath/ -> reason
        self.rule_excluded: Dict[str, str] = {}
        # staging collections from traversal
        self._depth_cutoffs: List[Tuple[str, int]] = []  # (relpath, cutoff_abs_depth)
        self._rule_excluded_candidates: Dict[str, str] = {}

def _walk_tree(root: Path, reports: Reports) -> List[str]:
    """Build the tree; collect candidates for reports."""
    lines: List[str] = [f"{root.name}/"]

    def walk(curr: Path, prefix: str, depth_from_root: int, rem_global: Optional[int], rem_override: Optional[int]) -> None:
        entries = _iter_entries(curr)

        # record rule-excluded candidates in this visible dir
        for e in entries:
            if not (e.is_dir() and not e.is_symlink()):
                continue
            rel = _to_posix_rel(e, root)
            reason: Optional[str] = None
            if _is_hidden(e) and not show_hidden:
                reason = "Hide hidden"
            elif not (_is_hidden(e) and show_hidden) and _matches_any(e.name, rel, _read_gitignore(root), True):
                reason = "gitignore list"
            elif _matches_any(e.name, rel, exclude_patterns, True):
                reason = "Exclusion list"
            ov = _override_for(e, rel, True)
            if ov == -1:
                reason = "Override (-1)"
            if reason:
                reports._rule_excluded_candidates[rel + "/"] = reason

        # visible set for printing and traversal
        visible: List[Path] = []
        for e in entries:
            rel = _to_posix_rel(e, root)
            if not _is_visible(e, rel):
                continue
            if only_dirs and not e.is_dir():
                continue
            visible.append(e)

        count = len(visible)
        for idx, p in enumerate(visible):
            is_last = idx == count - 1
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            rel = _to_posix_rel(p, root)
            is_link = p.is_symlink()
            try:
                is_dir = p.is_dir() and not is_link
            except Exception:
                is_dir = False

            display_name = f"{p.name}/" if is_dir else p.name
            lines.append(prefix + connector + display_name)

            if not is_dir:
                continue

            # decide budget
            ovd = _override_for(p, rel, True)
            if ovd == -1:
                continue
            rem_ov = _remaining_from_override(ovd) if ovd is not None else None
            eff_global = _effective_global_remaining(depth_from_root + 1)

            # override supersedes global
            if rem_ov is not None:
                if rem_ov <= 0:
                    # stop here due to override depth; do not count as depth-pruned (spec: only global)
                    continue
                walk(p, child_prefix, depth_from_root + 1, None, rem_ov - 1)
                continue

            # apply global
            if eff_global is None:
                walk(p, child_prefix, depth_from_root + 1, None, None)
            else:
                if eff_global <= 0:
                    # Stop due to global max_depth → record candidate for depth-pruned reporting
                    reports._depth_cutoffs.append((rel + "/", depth_from_root + 1))
                    continue
                walk(p, child_prefix, depth_from_root + 1, eff_global - 1, None)

    # Seed global remaining from max_depth
    start_rem = _effective_global_remaining(0)
    walk(root, "", 0, start_rem, None)
    return lines

def _compute_reports(root: Path, reports: Reports) -> None:
    """Compute heavy stats with granular per-directory progress before printing the tree."""
    # Build merged exclusion list once (after ROOT known)
    global _GITIGNORE, _EXCLUDES
    _GITIGNORE = _read_gitignore(root)
    _EXCLUDES = list(exclude_patterns) + _GITIGNORE

    # Depth-pruned (global) — compute stats
    print_progress("depth-pruned directories")
    extra_limit = _depth_limit_value_for_reports()
    dp_items = reports._depth_cutoffs
    # For console friendliness, show each directory being calculated
    for rel, cutoff_abs_depth in dp_items:
        display_rel = "/" + rel.strip("/") + "/"
        print_progress("depth-pruned directories", display_rel)
        p = root / Path(PurePosixPath(rel.strip("/")))
        if p.exists() and p.is_dir():
            rel_depth, f_dirs, f_files = _scan_stats(p, extra_limit)
            total_depth_abs = cutoff_abs_depth + rel_depth
            skipped_levels = total_depth_abs - cutoff_abs_depth
            if skipped_levels > 0:
                reports.depth_pruned[rel] = (total_depth_abs, skipped_levels, f_dirs, f_files)
    print_progress("depth-pruned directories", done=True)
    if reports.depth_pruned:
        _log(f"   └─ Analysing {len(reports.depth_pruned)} pruned branches...")

    # Rule-excluded — we compute totals with live updates
    print_progress("rule-excluded folders")
    reports.rule_excluded = dict(sorted(reports._rule_excluded_candidates.items(), key=lambda kv: kv[0].lower()))
    for rel, _reason in reports.rule_excluded.items():
        display_rel = "/" + rel.strip("/") + "/"
        print_progress("rule-excluded folders", display_rel)
        p = root / Path(PurePosixPath(rel.strip("/")))
        if p.exists() and p.is_dir():
            _ = _scan_stats(p, extra_limit)  # totals aggregated in renderer below for clarity
    print_progress("rule-excluded folders", done=True)
    if reports.rule_excluded:
        _log(f"   └─ Evaluating {len(reports.rule_excluded)} excluded folders...")

def _left_width(rows_left: List[str], header_left: str) -> int:
    lw = max([len(s) for s in rows_left] + [len(header_left), 35])
    return min(lw, 70)

def _rule(width: int) -> str:
    return "-" * width

def _render_depth_pruned(root: Path, reports: Reports) -> List[str]:
    out: List[str] = []
    if max_depth is None or max_depth == 0:
        return out

    title = f"Depth-Pruned Directories (max_depth={max_depth})"
    left_header = f"Folders @ Level {max_depth}:"
    right_header = "Full Directory Depth:"

    if not reports.depth_pruned:
        msg = f"No depth-pruned directories (max_depth={max_depth})"
        width = max(39, len(msg))
        out.extend([_rule(width), msg, _rule(width), ""])
        return out

    # Decide compression rule
    compress = (max_depth >= 6)

    # Sort and take first 4 for the table display
    items = sorted(reports.depth_pruned.items(), key=lambda kv: kv[0].lower())
    top = items[:4]

    rows_left: List[str] = []
    rows: List[Tuple[str, str]] = []
    skipped_folders_total = 0
    skipped_files_total = 0

    # Totals across all pruned branches
    for _, (_td, _sk, fdirs, ffiles) in items:
        skipped_folders_total += fdirs
        skipped_files_total += ffiles

    for rel, (total_depth_abs, skipped_levels, _fd, _ff) in top:
        display_path = _compress_path(rel) if compress else rel
        rows_left.append(display_path)
        right = f"{total_depth_abs} ({'1 level' if skipped_levels == 1 else f'{skipped_levels} levels'} skipped)"
        rows.append((display_path, right))

    left_w = _left_width(rows_left + [left_header], left_header)
    header_line = f"{left_header.ljust(left_w + 2)}{_TWO_TABS}{right_header}"
    width = max(len(title), len(header_line), 64)

    out.append(_rule(width))
    out.append(title)
    out.append(_rule(width))
    out.append(header_line)
    out.append(_rule(width))
    for l, r in rows:
        pad = " " * max(0, left_w - len(l))
        out.append(f"- {l}{pad}{_TWO_TABS}{r}")
    out.append(_rule(width))
    out.append(f"- Skipped Total: {_fmt_int(skipped_folders_total)} Folders | {_fmt_int(skipped_files_total)} Files")
    out.append(_rule(width))
    out.append("")
    return out

def _render_rule_excluded(root: Path, reports: Reports) -> List[str]:
    out: List[str] = []
    title = "Rule-Excluded Folders"
    left_header = "Excluded Folders:"
    right_header = "Rule Applied:"

    if not reports.rule_excluded:
        msg = "No rule-excluded folders (hidden, gitignore or exclusion list)"
        width = max(64, len(msg))
        out.extend([_rule(width), msg, _rule(width), ""])
        return out

    # Sort already done; show first 4 in table
    items = list(reports.rule_excluded.items())

    rows_left: List[str] = []
    rows: List[Tuple[str, str]] = []

    extra_limit = _depth_limit_value_for_reports()
    skipped_folders_total = 0
    skipped_files_total = 0

    # Table rows (top 4) with compression for long paths
    for rel, reason in items[:4]:
        rel_no_slash = rel.rstrip("/")
        display_path = _compress_path(rel) if len(rel_no_slash.split("/")) >= 6 else rel
        rows_left.append(display_path)
        rows.append((display_path, reason))

    # Totals across all excluded folders
    for rel, _reason in items:
        p = root / Path(PurePosixPath(rel.strip("/")))
        if p.exists() and p.is_dir():
            _d, fdirs, ffiles = _scan_stats(p, extra_limit)
            skipped_folders_total += fdirs
            skipped_files_total += ffiles

    left_w = _left_width(rows_left + [left_header], left_header)
    header_line = f"{left_header.ljust(left_w + 2)}{_TWO_TABS}{right_header}"
    width = max(len(title), len(header_line), 70)

    out.append(_rule(width))
    out.append(title)
    out.append(_rule(width))
    out.append(header_line)
    out.append(_rule(width))
    for l, r in rows:
        pad = " " * max(0, left_w - len(l))
        out.append(f"- {l}{pad}{_TWO_TABS}{r}")
    out.append(_rule(width))
    out.append(f"- Skipped Total: {_fmt_int(skipped_folders_total)} Folders | {_fmt_int(skipped_files_total)} Files")
    out.append(_rule(width))
    out.append("")
    return out

def _timestamped_filename(root: Path) -> str:
    ts = datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
    return f"{root.name}-{ts}.txt"

def _script_dir() -> Path:
    try:
        return Path(__file__).resolve().parent
    except Exception:
        return Path.cwd()

def _default_targets(root: Path) -> List[Path]:
    fname = _timestamped_filename(root)
    return [
        root / ".trees" / fname,
        _script_dir() / ".trees" / root.name / fname,
    ]

def _extra_targets(extra_dirs: List[str], root: Path) -> List[Path]:
    fname = _timestamped_filename(root)
    base = _script_dir() / ".trees" / root.name
    outs: List[Path] = []
    for s in extra_dirs:
        try:
            p = Path(s)
            if p.exists() and p.is_dir():
                outs.append(p / fname)
            else:
                outs.append(base / fname)
        except Exception:
            outs.append(base / fname)
    return outs

def _save(text: str, root: Path) -> List[Path]:
    targets = _default_targets(root) + _extra_targets(extra_save_dirs, root)
    saved: List[Path] = []
    for t in targets:
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
            saved.append(t)
        except Exception as e:
            print(f"Error writing {t}: {e}", file=sys.stderr)
    return saved

def main() -> None:
    _log("→ Normalising root folder path...")
    root_path = _normalise_root_folder(root_folder)

    if not root_path.exists() or not root_path.is_dir():
        sys.exit(f"Error: {root_path} is not a valid directory.")

    # Initialise global ROOT and merged patterns now that we have the real path
    global ROOT, _GITIGNORE, _EXCLUDES
    ROOT = root_path
    _GITIGNORE = _read_gitignore(ROOT)
    _EXCLUDES = list(exclude_patterns) + _GITIGNORE

    _log(f"→ Scanning directory tree for: {root_path}")
    _log("→ Building directory tree (please wait)...")

    reports = Reports()
    tree_lines = _walk_tree(ROOT, reports)

    if show_reports:
        _log("→ Generating reports (depth-pruned, rule-excluded)...")
        # Heavy computations with granular progress happen here, BEFORE printing the tree
        _compute_reports(ROOT, reports)

    # Compose output
    out_lines: List[str] = list(tree_lines)

    # Separation between tree and reports
    if show_reports:
        out_lines.append("")
        out_lines.append("")
        out_lines += _render_depth_pruned(ROOT, reports)
        out_lines += _render_rule_excluded(ROOT, reports)

    _log("→ Compiling skipped totals and preparing output...")
    final_text = "\n".join(out_lines)

    # Print to stdout
    print(final_text)

    _log("→ Saving reports to target folders...")
    saved_paths = _save(final_text, ROOT)
    if saved_paths:
        _log("→ Done. Reports saved successfully.\n")
        for p in saved_paths:
            print(f"  - {p}")

if __name__ == "__main__":
    main()
