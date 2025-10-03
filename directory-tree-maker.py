#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import sys
import fnmatch
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import List, Tuple

# ======================================
# USER CONFIGURATION - EDIT THIS SECTION
# ======================================

# Path to the root directory to traverse and render as a tree.
root_folder: Path = Path(r"C:\Users\Project_Folder").resolve()

# If True: list only directories (files are excluded). If False: list directories and files.
only_dirs: bool = False

# If True: include hidden entries (names beginning with "." on POSIX; best-effort on Windows).
# If False: hidden entries are excluded from the output.
show_hidden: bool = True

# Maximum recursion depth. None = no limit; 0 = only the root; N = root plus N levels.
max_depth: int | None = None

# If True: list directories before files in each directory. If False: interleave according to sort order.
list_dirs_first: bool = True

# If True: case-insensitive sorting (recommended). If False: case-sensitive sorting.
case_insensitive_sort: bool = True

# Glob patterns for entries to exclude entirely (not displayed). Matched against basename and POSIX-style relative path.
exclude_patterns: list[str] = ["*.mjs"]

# Glob patterns for directories to display but not descend into (shown as a single line).
# Typical heavy directories are included by default.
non_recursive_patterns: list[str] = [".git", ".*", "_*", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".DS_Store"]

# Glob patterns for hidden directories treated as non-recursive when hidden entries are shown.
hidden_non_recursive_patterns: list[str] = [".*"]

# Glob patterns for hidden directories that should be recursed into despite the non-recursive hidden policy.
hidden_recursive_exceptions: list[str] = []

# If non-empty and show_hidden=True, only hidden entries matching at least one of these patterns are included.
hidden_include_patterns: list[str] = []

# If True: treat all directories as non-recursive (displayed but not traversed).
non_recursive_catch_all: bool = False

# ----------------------------------------------------------
# OUTPUT LOCATIONS
# ----------------------------------------------------------
# Timestamped filename pattern: [rootname-YYYY.MM.DD.HH.MM.SS].txt
# Default behaviour: save to BOTH
#   A) root_folder/.trees/[rootname-TS].txt
#   B) <script_dir>/.trees/[rootname]/[rootname-TS].txt
# Additional save locations may be added to `extra_save_dirs`.
# Any invalid path falls back to (B).
extra_save_dirs: list[Path] = []  # e.g., [Path(r"D:\Backups\trees"), Path("/Users/louie/trees")]
# ======================================
# END OF CONFIGURATION SECTION
# ======================================


class Report:
    def __init__(self) -> None:
        self.skipped_due_to_depth_total: int = 0
        self.skipped_due_to_depth_examples: List[Tuple[str, int]] = []
        self.unreadable_dirs: List[str] = []
        self.saved_to: List[Path] = []
        self.fallbacks_used: int = 0


def to_posix_relpath(path: Path, root: Path) -> str:
    """Return the POSIX-style relative path from root ('' for the root itself)."""
    try:
        rel = path.relative_to(root)
        return "" if str(rel) == "." else str(PurePosixPath(rel.as_posix()))
    except Exception:
        rel = os.path.relpath(str(path), str(root))
        return "" if rel == "." else str(PurePosixPath(rel.replace(os.sep, "/")))


def _normcase(s: str) -> str:
    """Normalise case for matching. On Windows, make matching case-insensitive."""
    return s.casefold() if os.name == "nt" else s


def is_hidden(path: Path) -> bool:
    """Return True if the entry is hidden (POSIX: leading dot; Windows: FILE_ATTRIBUTE_HIDDEN when available)."""
    if path.name.startswith("."):
        return True
    if os.name == "nt":
        try:
            import ctypes  # standard library
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs == -1:
                return False
            return bool(attrs & 0x02)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            return False
    return False


def norm_sort_key(s: str) -> str:
    """Normalised sort key according to case sensitivity setting."""
    return s.lower() if case_insensitive_sort else s


def matches_any(name: str, relpath_posix: str, patterns: list[str], *, is_dir: bool = False) -> bool:
    """
    Glob-match against both basename and POSIX relative path.
    For directories, also match relpath with a trailing slash so '**/x/**' works at any level.
    Case-insensitive on Windows.
    """
    if not patterns:
        return False

    n = _normcase(name)
    r = _normcase(relpath_posix)
    candidates = [n, r]
    if is_dir:
        candidates.append(r + "/")  # allow '**/dir/**' and 'dir/' patterns

    for pat in patterns:
        p = _normcase(pat)
        for c in candidates:
            if fnmatch.fnmatchcase(c, p):
                return True
    return False


def should_show(path: Path, relpath_posix: str) -> bool:
    """Visibility decision (hidden policy and explicit excludes)."""
    name = path.name
    try:
        is_dir = path.is_dir() and not path.is_symlink()
    except Exception:
        is_dir = False

    hidden = is_hidden(path)

    if hidden and not show_hidden:
        return False

    if hidden and show_hidden and hidden_include_patterns:
        if not matches_any(name, relpath_posix, hidden_include_patterns, is_dir=is_dir):
            return False

    if matches_any(name, relpath_posix, exclude_patterns, is_dir=is_dir):
        return False

    return True


def should_descend_dir(dir_path: Path, depth: int, root: Path) -> tuple[bool, str]:
    """
    Recursion decision for directories. Returns (descend?, reason).
    Reasons: "", "max_depth", "catch_all", "non_recursive", "hidden_non_recursive", "symlink".
    """
    name = dir_path.name
    rel = to_posix_relpath(dir_path, root)

    try:
        if dir_path.is_symlink():
            return False, "symlink"
    except Exception:
        return False, "symlink"

    if max_depth is not None and depth >= max_depth:
        return False, "max_depth"

    if non_recursive_catch_all:
        return False, "catch_all"

    if matches_any(name, rel, non_recursive_patterns, is_dir=True):
        return False, "non_recursive"

    if show_hidden and is_hidden(dir_path):
        if matches_any(name, rel, hidden_non_recursive_patterns, is_dir=True):
            if not matches_any(name, rel, hidden_recursive_exceptions, is_dir=True):
                return False, "hidden_non_recursive"

    return True, ""


def iter_entries(directory: Path) -> List[Path]:
    """Return directory entries, sorted according to configuration."""
    entries = list(directory.iterdir())
    if list_dirs_first:
        dirs = [p for p in entries if p.is_dir() and not p.is_symlink()]
        others = [p for p in entries if not (p.is_dir() and not p.is_symlink())]
        dirs.sort(key=lambda p: norm_sort_key(p.name))
        others.sort(key=lambda p: norm_sort_key(p.name))
        return dirs + others
    entries.sort(key=lambda p: norm_sort_key(p.name))
    return entries


def build_tree(root: Path) -> Tuple[List[str], Report]:
    """Build the tree representation starting at root and return (lines, report)."""
    report = Report()
    lines: List[str] = [f"{root.name}/"]

    def walk(current: Path, prefix: str, depth: int) -> None:
        try:
            entries = iter_entries(current)
        except Exception:
            lines.append(prefix + "⟨permission denied⟩")
            report.unreadable_dirs.append(to_posix_relpath(current, root) or ".")
            return

        displayable = []
        for p in entries:
            rel = to_posix_relpath(p, root)
            if should_show(p, rel):
                if only_dirs and not p.is_dir():
                    continue
                displayable.append(p)

        count = len(displayable)
        for idx, path in enumerate(displayable):
            is_last = (idx == count - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            rel = to_posix_relpath(path, root)
            name = path.name
            is_link = path.is_symlink()
            try:
                is_dir = path.is_dir() and not is_link
            except Exception:
                is_dir = False

            if is_link:
                try:
                    target = os.readlink(path)
                except OSError:
                    target = "?"
                display = f"{name} -> {target}/"
            else:
                display = f"{name}/" if is_dir else name

            lines.append(prefix + connector + display)

            if is_dir:
                descend, reason = should_descend_dir(path, depth + 1, root)
                if descend:
                    walk(path, child_prefix, depth + 1)
                elif reason == "max_depth":
                    report.skipped_due_to_depth_total += 1
                    report.skipped_due_to_depth_examples.append((rel or ".", depth + 1))

    walk(root, prefix="", depth=0)
    return lines, report


# ------------------------ Saving ------------------------

def _timestamped_filename(root: Path) -> str:
    """Return '[rootname-YYYY.MM.DD.HH.MM.SS].txt'."""
    ts = datetime.now().strftime("%Y.%m.%d.%H.%M.%S")
    return f"{root.name}-{ts}.txt"


def _script_dir() -> Path:
    """Directory where this script resides."""
    try:
        return Path(__file__).resolve().parent
    except Exception:
        return Path.cwd()


def _default_save_paths(root: Path) -> list[Path]:
    """
    Default destinations:
      A) root/.trees/[filename]
      B) <script_dir>/.trees/[rootname]/[filename]
    """
    fname = _timestamped_filename(root)
    a = root / ".trees" / fname
    b = _script_dir() / ".trees" / root.name / fname
    return [a, b]


def _expand_extra_saves(extra_dirs: list[Path], root: Path) -> list[Path]:
    """
    Expand extra save directories to full file paths.
    Invalid base directories fall back to the script_dir default (B).
    """
    targets: list[Path] = []
    fallback_base = _script_dir() / ".trees" / root.name
    fname = _timestamped_filename(root)

    for base in extra_dirs:
        try:
            base = Path(base)
            # If base exists and is a directory, use it; otherwise fallback.
            if base.exists() and base.is_dir():
                targets.append(base / fname)
            else:
                targets.append(fallback_base / fname)
        except Exception:
            targets.append(fallback_base / fname)
    return targets


def save_outputs(lines: List[str], root: Path, extra_dirs: list[Path]) -> Report:
    """Write the tree text to all configured destinations; return a report with locations saved."""
    report = Report()
    text = "\n".join(lines)

    targets = _default_save_paths(root) + _expand_extra_saves(extra_dirs, root)

    # Ensure directories exist and write files.
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            report.saved_to.append(target)
        except Exception:
            # If target is not under script_dir default (B), fallback there.
            fallback = _script_dir() / ".trees" / root.name / target.name
            try:
                fallback.parent.mkdir(parents=True, exist_ok=True)
                fallback.write_text(text, encoding="utf-8")
                report.saved_to.append(fallback)
                report.fallbacks_used += 1
            except Exception:
                # Silent failure is avoided: still print to stderr.
                print(f"Error: failed to write '{target}' and fallback '{fallback}'", file=sys.stderr)

    return report


# ------------------------ Main ------------------------

def main() -> None:
    if not root_folder.exists() or not root_folder.is_dir():
        sys.exit(f"Error: {root_folder} is not a directory")

    lines, traversal_report = build_tree(root_folder)

    # Always print to stdout.
    print("\n".join(lines))

    # Save to default locations and configured extra locations.
    save_report = save_outputs(lines, root_folder, extra_save_dirs)

    # Post-run notes.
    if traversal_report.skipped_due_to_depth_total:
        print(
            f"\nWarning: max_depth blocked {traversal_report.skipped_due_to_depth_total} directories",
            file=sys.stderr,
        )
        for rel, d in traversal_report.skipped_due_to_depth_examples[:10]:
            print(f"  - {rel} @ {d}", file=sys.stderr)

    if traversal_report.unreadable_dirs:
        print("\nUnreadable directories:", file=sys.stderr)
        for rel in traversal_report.unreadable_dirs[:10]:
            print(f"  - {rel}", file=sys.stderr)

    # Report save locations.
    if save_report.saved_to:
        print("\nSaved tree to:", file=sys.stderr)
        for p in save_report.saved_to:
            print(f"  - {p}", file=sys.stderr)
        if save_report.fallbacks_used:
            print(f"(Fallbacks used: {save_report.fallbacks_used})", file=sys.stderr)


if __name__ == "__main__":
    main()
