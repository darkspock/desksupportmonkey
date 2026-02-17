#!/usr/bin/env python3
"""
Architecture compliance checks for CI and git hooks.

Validates DDD + CQRS + Clean Architecture rules:
- Commands must not return values
- Queries must not have side effects (no save/delete calls)
- Domain layer must not import infrastructure
- Routers must not import repositories directly
- No cross-bounded-context repository access

Usage:
    python scripts/check_architecture.py          # Check all
    python scripts/check_architecture.py --quick   # Only critical checks
"""

import ast
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
ADAPTERS = ROOT / "adapters"


@dataclass
class Violation:
    file: str
    line: int
    rule: str
    message: str
    severity: str  # critical, high, medium


@dataclass
class CheckResult:
    violations: list[Violation] = field(default_factory=list)
    files_checked: int = 0

    @property
    def passed(self) -> bool:
        return not any(v.severity == "critical" for v in self.violations)

    def add(self, file: str, line: int, rule: str, message: str, severity: str = "critical"):
        rel = os.path.relpath(file, ROOT)
        self.violations.append(Violation(rel, line, rule, message, severity))


def parse_file(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(), filename=str(path))
    except SyntaxError:
        return None


# ---------------------------------------------------------------------------
# Check 1: Command handlers must return None
# ---------------------------------------------------------------------------
def check_commands_return_none(result: CheckResult):
    """Commands must not return values (CQRS rule #4)."""
    commands_dir = list(SRC.rglob("application/commands/*.py"))
    for path in commands_dir:
        if path.name == "__init__.py":
            continue
        result.files_checked += 1
        tree = parse_file(path)
        if not tree:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.name.endswith("CommandHandler"):
                continue
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if item.name != "handle":
                    continue
                # Check return annotation
                if item.returns:
                    ann = ast.dump(item.returns)
                    if "None" not in ann:
                        result.add(
                            str(path), item.lineno,
                            "CQRS-CMD-RETURN",
                            f"{node.name}.handle() has return type annotation (should be None)",
                        )
                # Check for return statements with values
                for child in ast.walk(item):
                    if isinstance(child, ast.Return) and child.value is not None:
                        result.add(
                            str(path), child.lineno,
                            "CQRS-CMD-RETURN",
                            f"{node.name}.handle() returns a value (commands must return None)",
                        )


# ---------------------------------------------------------------------------
# Check 2: Domain layer must not import infrastructure
# ---------------------------------------------------------------------------
def check_domain_no_infra_imports(result: CheckResult):
    """Domain layer must not import from infrastructure or adapters."""
    domain_files = list(SRC.rglob("domain/*.py"))
    forbidden = ("infrastructure", "adapters", "sqlalchemy", "redis", "celery")
    for path in domain_files:
        if path.name == "__init__.py":
            continue
        result.files_checked += 1
        tree = parse_file(path)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(f in alias.name for f in forbidden):
                        result.add(
                            str(path), node.lineno,
                            "LAYER-DOMAIN-IMPORT",
                            f"Domain imports forbidden module: {alias.name}",
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                if any(f in node.module for f in forbidden):
                    result.add(
                        str(path), node.lineno,
                        "LAYER-DOMAIN-IMPORT",
                        f"Domain imports from forbidden module: {node.module}",
                    )


# ---------------------------------------------------------------------------
# Check 3: Routers must not import repository implementations
# ---------------------------------------------------------------------------
def check_routers_no_direct_repo(result: CheckResult):
    """Routers should not directly instantiate repository implementations."""
    router_files = list(ADAPTERS.rglob("routers.py"))
    for path in router_files:
        result.files_checked += 1
        content = path.read_text()
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Check for Repository() instantiation inside route functions
            stripped = line.strip()
            if "Repository(" in stripped and not stripped.startswith(("#", "//", "def", "class")):
                if "import" not in stripped:
                    result.add(
                        str(path), i,
                        "HTTP-DIRECT-REPO",
                        f"Router instantiates repository directly: {stripped[:80]}",
                        severity="high",
                    )


# ---------------------------------------------------------------------------
# Check 4: No cross-BC repository imports
# ---------------------------------------------------------------------------
def check_no_cross_bc_repo(result: CheckResult):
    """Application layer must not import repositories from other bounded contexts."""
    app_files = list(SRC.rglob("application/**/*.py"))
    for path in app_files:
        if path.name == "__init__.py":
            continue
        result.files_checked += 1
        # Determine this file's BC
        rel = path.relative_to(SRC)
        parts = rel.parts
        if len(parts) < 2:
            continue
        own_bc = parts[0]  # e.g. "auth_bc"

        tree = parse_file(path)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if ".infrastructure.repository" in node.module:
                    # Importing a concrete repository in application layer
                    result.add(
                        str(path), node.lineno,
                        "LAYER-APP-INFRA",
                        f"Application layer imports infrastructure: {node.module}",
                        severity="high",
                    )
                if ".infrastructure.repository" in node.module or ".domain.repository" in node.module:
                    # Check if it's from another BC
                    if node.module.startswith("src."):
                        import_bc = node.module.split(".")[1]
                    else:
                        import_bc = node.module.split(".")[0]
                    if import_bc != own_bc and import_bc.endswith("_bc"):
                        result.add(
                            str(path), node.lineno,
                            "BC-CROSS-IMPORT",
                            f"Cross-BC repository access: {own_bc} imports from {import_bc}",
                        )


# ---------------------------------------------------------------------------
# Check 5: Query handlers must not call save/delete
# ---------------------------------------------------------------------------
def check_queries_no_side_effects(result: CheckResult):
    """Query handlers must not have side effects (no save, delete, commit)."""
    query_files = list(SRC.rglob("application/queries/*.py"))
    forbidden_calls = ("save", "delete", "commit", "flush", "execute")
    for path in query_files:
        if path.name == "__init__.py":
            continue
        result.files_checked += 1
        tree = parse_file(path)
        if not tree:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.name.endswith("QueryHandler"):
                continue
            for item in ast.walk(node):
                if isinstance(item, ast.Call):
                    if isinstance(item.func, ast.Attribute):
                        if item.func.attr in forbidden_calls:
                            result.add(
                                str(path), item.lineno,
                                "CQRS-QUERY-SIDE-EFFECT",
                                f"{node.name} calls .{item.func.attr}() (queries must be read-only)",
                            )


# ---------------------------------------------------------------------------
# Check 6: No business logic in routers (function body too long)
# ---------------------------------------------------------------------------
def check_router_function_length(result: CheckResult):
    """Router functions should be thin (max 30 lines)."""
    router_files = list(ADAPTERS.rglob("routers.py"))
    max_lines = 30
    for path in router_files:
        result.files_checked += 1
        tree = parse_file(path)
        if not tree:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_lines = (node.end_lineno or node.lineno) - node.lineno
                if body_lines > max_lines:
                    result.add(
                        str(path), node.lineno,
                        "HTTP-FAT-ROUTER",
                        f"Function '{node.name}' is {body_lines} lines (max {max_lines})",
                        severity="medium",
                    )


def main():
    quick = "--quick" in sys.argv
    result = CheckResult()

    # Critical checks (always run)
    check_commands_return_none(result)
    check_domain_no_infra_imports(result)
    check_queries_no_side_effects(result)
    check_no_cross_bc_repo(result)

    if not quick:
        # Additional checks
        check_routers_no_direct_repo(result)
        check_router_function_length(result)

    # Report
    critical = [v for v in result.violations if v.severity == "critical"]
    high = [v for v in result.violations if v.severity == "high"]
    medium = [v for v in result.violations if v.severity == "medium"]

    print(f"\n{'='*60}")
    print(f"  Architecture Check — {result.files_checked} files scanned")
    print(f"{'='*60}\n")

    if not result.violations:
        print("  All checks passed.\n")
        sys.exit(0)

    for severity, label, violations in [
        ("critical", "CRITICAL", critical),
        ("high", "HIGH", high),
        ("medium", "MEDIUM", medium),
    ]:
        if not violations:
            continue
        print(f"  [{label}] {len(violations)} violation(s)\n")
        for v in violations:
            print(f"    {v.file}:{v.line}")
            print(f"      [{v.rule}] {v.message}\n")

    total = len(result.violations)
    print(f"{'='*60}")
    print(f"  Total: {total} violations ({len(critical)} critical, {len(high)} high, {len(medium)} medium)")

    if critical:
        print(f"  Status: FAILED (critical violations found)")
        print(f"{'='*60}\n")
        sys.exit(1)
    else:
        print(f"  Status: PASSED (no critical violations)")
        print(f"{'='*60}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
