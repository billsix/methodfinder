#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# SHARED, VENDORED TOOL -- keep every copy byte-identical.
# Canonical: runClaudeInContainer tasks/reference/check_local_annotations.py
#   (github.com/billsix/runClaudeInContainer). Edit the canonical, then re-copy
#   it over every vendored copy.
# Vendored into each PYTHON project's tools/ so the project's own CI is
#   self-contained (a public repo can't rely on a mounted ~/.claude). Pure
#   C/C++/asm repos do not vendor it.
# Enforces the "annotate every binding" rule from python-coding-standard.md
#   (the completeness check `ty` cannot do); `make type-check` runs it.
# ---------------------------------------------------------------------------
"""Flag local variables that lack an explicit type annotation.

`ty` infers local types and never requires an annotation, and ruff's
flake8-annotations rules cover only function signatures -- so nothing off the
shelf enforces the house rule that locals are annotated too (the rule's origin:
github.com/billsix/modelviewprojection
`tasks/archive/2026/09/17/annotate-all-local-variables.md`).  This does.

A finding is a plain ``name = ...`` assignment inside a function whose ``name``
is never given an annotation anywhere in that same function (an ``AnnAssign``
like ``name: T = ...`` or an annotated parameter).  So annotating a name once
covers all its later re-binds.

Deliberately NOT flagged (can't carry an inline annotation, or aren't ours):
tuple/list unpack targets, attribute/subscript targets (``self.x = ...``),
augmented assignment (``x += 1``), ``for`` / ``with as`` / ``except as`` /
comprehension / walrus targets, and module-level assignments (the rule is about
*local* variables).  Nested functions are checked in their own scope.

Usage (paths are files or dirs; default ``src``):
    python tools/check_local_annotations.py [--include-module] [path ...]
Exit status: 0 when no finding is reported, 1 when any is, and 2 when a given
path does not exist or no ``.py`` file matches (so a typo in a gate's path
fails the gate instead of passing it).  Run it in the container:
    make shell-exec CMD='python tools/check_local_annotations.py src'
"""

from __future__ import annotations

import ast
import pathlib
import sys


def _annotated_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names that carry an annotation somewhere in ``fn``'s own scope: annotated
    params, plus ``AnnAssign`` targets not inside a nested function."""
    names: set[str] = set()
    args: ast.arguments = fn.args
    for a in (
        *args.posonlyargs,
        *args.args,
        *args.kwonlyargs,
        args.vararg,
        args.kwarg,
    ):
        if a is not None and a.annotation is not None:
            names.add(a.arg)
    for node in _own_scope_nodes(fn):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _own_scope_nodes(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.AST]:
    """Every node lexically inside ``fn`` but NOT inside a nested def/lambda/
    class (those have their own scopes).  Comprehension bodies are kept: they
    hold no ``Assign`` nodes, so they cannot produce a finding.

    A ``class`` body nested in ``fn`` is filtered out too: its assignments are
    class attributes / enum members, not locals of ``fn`` (annotating them
    would change their meaning), and its methods are separate scopes that
    ``check_file``'s own walk visits independently.
    """
    out: list[ast.AST] = []
    for stmt in fn.body:
        out.extend(ast.walk(stmt))
    # Drop anything that lives inside a nested scope (ast.walk descends into
    # nested functions/lambdas/classes too, so filter their subtrees out).
    nested: set[int] = set()
    for stmt in fn.body:
        for node in ast.walk(stmt):
            if node is not fn and isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.Lambda,
                    ast.ClassDef,
                ),
            ):
                for inner in ast.walk(node):
                    if inner is not node:
                        nested.add(id(inner))
    return [n for n in out if id(n) not in nested]


def check_file(path: pathlib.Path) -> list[tuple[int, str]]:
    """Un-annotated local ``name = ...`` assignments in every function of a file.

    Args:
        path: The Python source file to check.

    Returns:
        Sorted ``(line, name)`` pairs, one per finding.
    """
    tree: ast.Module = ast.parse(path.read_text(), filename=str(path))
    findings: list[tuple[int, str]] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        annotated: set[str] = _annotated_names(fn)
        scope: list[ast.AST] = _own_scope_nodes(fn)
        # A name declared `global`/`nonlocal` in this function is NOT a local of
        # it -- it rebinds a module/enclosing variable annotated at THAT scope,
        # and Python forbids annotating a global/nonlocal-declared name
        # (`SyntaxError: annotated name can't be global`).  So skip them here.
        declared_elsewhere: set[str] = {
            name
            for node in scope
            if isinstance(node, (ast.Global, ast.Nonlocal))
            for name in node.names
        }
        for node in scope:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id not in annotated
                    and target.id not in declared_elsewhere
                ):
                    findings.append((node.lineno, target.id))
    return sorted(set(findings))


def _module_scope_nodes(tree: ast.Module) -> list[ast.AST]:
    """Every node at MODULE scope -- lexically in the module but NOT inside a
    def/lambda/class (those have their own scopes).  Includes assignments inside
    top-level ``if``/``for``/``while``/``with``/``try`` blocks, which still run
    at import and bind module globals."""
    out: list[ast.AST] = []
    for stmt in tree.body:
        out.extend(ast.walk(stmt))
    nested: set[int] = set()
    for stmt in tree.body:
        for node in ast.walk(stmt):
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.Lambda,
                    ast.ClassDef,
                ),
            ):
                for inner in ast.walk(node):
                    if inner is not node:
                        nested.add(id(inner))
    return [n for n in out if id(n) not in nested]


def check_file_module(path: pathlib.Path) -> list[tuple[int, str]]:
    """Module-level (global) ``name = ...`` assignments lacking an annotation.

    Same exemptions as locals (tuple-unpack / ``for`` / ``with as`` / ``except
    as`` / comprehension / walrus / augmented / attribute-or-subscript targets);
    annotating a name once at module scope covers its later re-binds."""
    tree: ast.Module = ast.parse(path.read_text(), filename=str(path))
    scope: list[ast.AST] = _module_scope_nodes(tree)
    annotated: set[str] = {
        n.target.id
        for n in scope
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    }
    findings: list[tuple[int, str]] = []
    for node in scope:
        if not isinstance(node, ast.Assign):
            continue
        # A `TypeVar`/`ParamSpec`/`TypeVarTuple` definition cannot carry an
        # annotation (`X: TypeVar = TypeVar(...)` makes the type checker stop
        # treating X as a type variable), so don't flag it.
        if isinstance(node.value, ast.Call):
            func: ast.expr = node.value.func
            fname: str = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else ""
            )
            if fname in ("TypeVar", "ParamSpec", "TypeVarTuple"):
                continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id not in annotated:
                findings.append((node.lineno, target.id))
    return sorted(set(findings))


def iter_py(paths: list[str]) -> list[pathlib.Path]:
    """The ``.py`` files named by ``paths``: files as given, directories recursively.

    Args:
        paths: Files or directories.

    Returns:
        The matching files, each directory's in sorted order.

    Raises:
        FileNotFoundError: A path does not exist.

    >>> iter_py(["/no/such/path"])
    Traceback (most recent call last):
    ...
    FileNotFoundError: /no/such/path
    """
    files: list[pathlib.Path] = []
    for p in paths:
        pp: pathlib.Path = pathlib.Path(p)
        if pp.is_dir():
            files.extend(sorted(pp.rglob("*.py")))
        elif pp.is_file():
            if pp.suffix == ".py":
                files.append(pp)
        else:
            raise FileNotFoundError(p)
    return files


def display_path(f: pathlib.Path, root: pathlib.Path) -> pathlib.Path:
    """``f`` relative to ``root`` when it lies under it, else ``f`` as given.

    Args:
        f: A file being reported.
        root: The repository root (the parent of this script's directory).

    Returns:
        The path to print.

    >>> display_path(pathlib.Path("/elsewhere/x.py"), pathlib.Path("/repo"))
    PosixPath('/elsewhere/x.py')
    """
    resolved: pathlib.Path = f.resolve()
    return resolved.relative_to(root) if resolved.is_relative_to(root) else f


def main() -> int:
    """Check the paths on the command line and print each finding.

    Returns:
        0 if clean, 1 if any binding lacks an annotation, 2 if a path does not
        exist or no ``.py`` file matched.
    """
    root: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]
    argv: list[str] = sys.argv[1:]
    # --include-module also flags module-level (global) un-annotated assigns, not
    # just locals.  Off by default so the src/tests gate stays locals-only.
    include_module: bool = "--include-module" in argv
    args: list[str] = [a for a in argv if a != "--include-module"] or ["src"]
    try:
        files: list[pathlib.Path] = iter_py(args)
    except FileNotFoundError as missing:
        print(f"check_local_annotations: no such path: {missing}", file=sys.stderr)
        return 2
    if not files:
        print(
            f"check_local_annotations: no .py file under {' '.join(args)}",
            file=sys.stderr,
        )
        return 2
    total: int = 0
    for f in files:
        rel: pathlib.Path = display_path(f, root)
        for lineno, name in check_file(f):
            print(f"{rel}:{lineno}: local '{name}' lacks a type annotation")
            total += 1
        if include_module:
            for lineno, name in check_file_module(f):
                print(f"{rel}:{lineno}: module-level '{name}' lacks a type annotation")
                total += 1
    if total:
        print(f"\n{total} un-annotated binding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
