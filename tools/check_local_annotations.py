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
shelf enforces the house rule that locals are annotated too
(`tasks/annotate-all-local-variables.md`).  This does.

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
    python tools/check_local_annotations.py [path ...]
Exit status is nonzero if any finding is reported.  Run it in the container:
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
    args = fn.args
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
        if isinstance(node, ast.AnnAssign) and isinstance(
            node.target, ast.Name
        ):
            names.add(node.target.id)
    return names


def _own_scope_nodes(
    fn: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.AST]:
    """Every node lexically inside ``fn`` but NOT inside a nested def/lambda/
    class/comprehension (those have their own scopes).

    A ``class`` body nested in ``fn`` is filtered out too: its assignments are
    class attributes / enum members, not locals of ``fn`` (annotating them
    would change their meaning), and its methods are separate scopes that
    ``check_file``'s own walk visits independently.
    """
    out: list[ast.AST] = []
    for stmt in fn.body:
        for node in ast.walk(stmt):
            out.append(node)
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
    tree = ast.parse(path.read_text(), filename=str(path))
    findings: list[tuple[int, str]] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        annotated = _annotated_names(fn)
        scope = _own_scope_nodes(fn)
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
        for node in ast.walk(stmt):
            out.append(node)
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
    tree = ast.parse(path.read_text(), filename=str(path))
    scope = _module_scope_nodes(tree)
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
            func = node.value.func
            fname = (
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
    files: list[pathlib.Path] = []
    for p in paths:
        pp = pathlib.Path(p)
        if pp.is_dir():
            files.extend(sorted(pp.rglob("*.py")))
        elif pp.suffix == ".py":
            files.append(pp)
    return files


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    argv: list[str] = sys.argv[1:]
    # --include-module also flags module-level (global) un-annotated assigns, not
    # just locals.  Off by default so the src/tests gate stays locals-only.
    include_module: bool = "--include-module" in argv
    args: list[str] = [a for a in argv if a != "--include-module"] or ["src"]
    total: int = 0
    for f in iter_py(args):
        rel = f.resolve().relative_to(root)
        for lineno, name in check_file(f):
            print(f"{rel}:{lineno}: local '{name}' lacks a type annotation")
            total += 1
        if include_module:
            for lineno, name in check_file_module(f):
                print(
                    f"{rel}:{lineno}: module-level '{name}' "
                    "lacks a type annotation"
                )
                total += 1
    if total:
        print(f"\n{total} un-annotated binding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
