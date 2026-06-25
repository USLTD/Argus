"""
Declarative rule parser and ``CompatContext`` for the ``compatible`` field in
METADATA.

Grammar::

    rule       := expression '->' confidence
    expression := comparison ( ('AND' | 'OR') comparison )*
    comparison := identifier operator value
    identifier := [a-zA-Z_][a-zA-Z0-9_.]*
    operator   := EQ | NEQ | GT | LT | GTE | LTE | LIKE | STARTSWITH | ENDSWITH
                | == | != | > | < | >= | <=
    value      := SQUOTED | DQUOTED
    confidence := INCOMPATIBLE | LOW | MEDIUM | HIGH | FULL | TRUE | FALSE | UNKNOWN
"""

from __future__ import annotations

import fnmatch
import os
import platform as _platform_mod
import re
import sys as _sys_mod
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import ModuleType
from collections.abc import Callable
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from backend.interfaces.caps import StaticSystemInfo
    from backend.storage.config import ArgusConfig

from .enums import ConfidenceScore

# ---------------------------------------------------------------------------
# Operator definitions
# ---------------------------------------------------------------------------

_OPERATORS: dict[str, str] = {
    "EQ": "eq",
    "NEQ": "ne",
    "GT": "gt",
    "LT": "lt",
    "GTE": "ge",
    "LTE": "le",
    "LIKE": "like",
    "STARTSWITH": "startswith",
    "ENDSWITH": "endswith",
    "==": "eq",
    "!=": "ne",
    ">": "gt",
    "<": "lt",
    ">=": "ge",
    "<=": "le",
}

_OP_PATTERN = "|".join(sorted(_OPERATORS, key=len, reverse=True))

_RULE_RE = re.compile(r"^\s*(?P<expr>.+?)\s*->\s*(?P<confidence>\S+)\s*$")

_COMP_RE = re.compile(
    r"^\s*(?P<ident>[a-zA-Z_][a-zA-Z0-9_.]*)\s+"
    r"(?P<op>" + _OP_PATTERN + r")\s+"
    r"(?P<value>'[^']*'|\"[^\"]*\")\s*$"
)

_AND_OR_RE = re.compile(r"\s+(AND|OR)\s+")

# ---------------------------------------------------------------------------
# Resolved context values  (flat identifier → value)
# ---------------------------------------------------------------------------

_IDENTIFIER_LAMBDA_MAP: dict[str, Callable[[str, CompatContext], object]] = {}


def _reg(name: str) -> Callable[[Callable[[str, CompatContext], object]], Callable[[str, CompatContext], object]]:
    def deco(fn: Callable[[str, CompatContext], object]) -> Callable[[str, CompatContext], object]:
        _IDENTIFIER_LAMBDA_MAP[name] = fn
        return fn

    return deco


# ---------------------------------------------------------------------------
# CompatContext  —  pre-evaluated platform / sys / os values
# ---------------------------------------------------------------------------


@dataclass
class SysInfo:
    platform: str
    maxsize: int
    byteorder: str
    version: str


@dataclass
class PlatformInfo:
    system: str
    machine: str
    release: str
    version: str
    python_version: str
    python_implementation: str
    processor: str
    arch_bits: str


@dataclass
class OsInfo:
    name: str
    sep: str


@dataclass
class CompatContext:
    sys: SysInfo
    platform: PlatformInfo
    os: OsInfo
    math: ModuleType


def build_compat_context() -> CompatContext:
    vi = _sys_mod.version_info
    arch_bits, _ = _platform_mod.architecture()
    return CompatContext(
        sys=SysInfo(
            platform=_sys_mod.platform,
            maxsize=_sys_mod.maxsize,
            byteorder=_sys_mod.byteorder,
            version=f"{vi.major}.{vi.minor}.{vi.micro}",
        ),
        platform=PlatformInfo(
            system=_platform_mod.system(),
            machine=_platform_mod.machine(),
            release=_platform_mod.release(),
            version=_platform_mod.version(),
            python_version=_platform_mod.python_version(),
            python_implementation=_platform_mod.python_implementation(),
            processor=_platform_mod.processor(),
            arch_bits=arch_bits,
        ),
        os=OsInfo(
            name=os.name,
            sep=os.sep,
        ),
        math=_sys_mod.modules.get("math") or __import__("math"),
    )


# Register identifiers so the declarative parser can resolve them.
# (Kept close to the dataclass definition for maintainability.)


@_reg("sys.platform")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.sys.platform


@_reg("sys.maxsize")
def _(_: str, ctx: CompatContext) -> int:
    return ctx.sys.maxsize


@_reg("sys.byteorder")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.sys.byteorder


@_reg("sys.version")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.sys.version


@_reg("platform.system")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.system


@_reg("platform.machine")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.machine


@_reg("platform.release")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.release


@_reg("platform.version")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.version


@_reg("platform.python_version")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.python_version


@_reg("platform.python_implementation")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.python_implementation


@_reg("platform.processor")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.processor


@_reg("platform.arch_bits")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.platform.arch_bits


@_reg("os.name")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.os.name


@_reg("os.sep")
def _(_: str, ctx: CompatContext) -> str:
    return ctx.os.sep


def _resolve_identifier(ident: str, ctx: CompatContext) -> object:
    fn = _IDENTIFIER_LAMBDA_MAP.get(ident)
    if fn is None:
        raise ValueError(f"Unknown identifier '{ident}' in compatibility rule")
    return fn(ident, ctx)


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

_CONFIDENCE_STR_MAP: dict[str, ConfidenceScore] = {
    "FULL": ConfidenceScore.FULL,
    "HIGH": ConfidenceScore.HIGH,
    "MEDIUM": ConfidenceScore.MEDIUM,
    "LOW": ConfidenceScore.LOW,
    "INCOMPATIBLE": ConfidenceScore.INCOMPATIBLE,
}


def _eval_value(raw: str) -> str:
    """Strip surrounding quotes from a raw value token."""
    return raw[1:-1]


def _eval_comparison(ident: str, op: str, raw_value: str, ctx: CompatContext) -> bool:
    actual = _resolve_identifier(ident, ctx)
    expected = _eval_value(raw_value)

    op_key = _OPERATORS[op]

    if op_key == "eq":
        return str(actual) == expected
    if op_key == "ne":
        return str(actual) != expected
    if op_key == "gt":
        return str(actual) > expected
    if op_key == "lt":
        return str(actual) < expected
    if op_key == "ge":
        return str(actual) >= expected
    if op_key == "le":
        return str(actual) <= expected
    if op_key == "like":
        return fnmatch.fnmatch(str(actual), expected)
    if op_key == "startswith":
        return str(actual).startswith(expected)
    if op_key == "endswith":
        return str(actual).endswith(expected)

    raise ValueError(f"Unknown operator: {op}")


def evaluate_rules(rules: list[str], ctx: CompatContext) -> str | None:
    """Evaluate declarative rules against *ctx*. Returns the confidence label
    (e.g. ``"FULL"``, ``"TRUE"``) of the first matching rule, or ``None`` when
    no rule matches."""
    for rule in rules:
        m = _RULE_RE.match(rule)
        if not m:
            raise ValueError(f"Malformed compatibility rule: {rule!r}")
        expr = m.group("expr")
        confidence = m.group("confidence")

        tokens = _AND_OR_RE.split(expr.strip())
        result: bool | None = None
        expect_and = True  # The first token is always just a comparison

        for token in tokens:
            token = token.strip()
            if token == "AND":
                expect_and = True
                continue
            if token == "OR":
                expect_and = False
                continue

            cm = _COMP_RE.match(token)
            if not cm:
                raise ValueError(f"Malformed comparison in rule: {token!r}")
            comp_result = _eval_comparison(
                cm.group("ident"), cm.group("op"), cm.group("value"), ctx
            )

            if result is None:
                result = comp_result
            elif expect_and:
                result = result and comp_result
            else:
                result = result or comp_result

        if result:
            return confidence

    return None


def evaluate_compatible(
    compatible: list[str] | Callable[[CompatContext], ConfidenceScore | None] | None,
    ctx: CompatContext | None,
) -> ConfidenceScore | None:
    """Shorthand that accepts any valid *compatible* value and returns the
    corresponding :class:`ConfidenceScore` (or ``None`` for drivers whose
    callable returned ``None`` or whose declarative rules didn't match).

    This is the entry point used by the **driver** loader."""
    if compatible is None or ctx is None:
        return None
    if callable(compatible):
        return compatible(ctx)
    label = evaluate_rules(compatible, ctx)
    if label is None:
        return None
    return _CONFIDENCE_STR_MAP.get(label)


def evaluate_script_compatible(
    compatible: list[str] | None,
    ctx: CompatContext,
) -> bool | None:
    """Evaluate *compatible* for a **Lua script**.

    Returns:
        ``True`` — load, ``False`` — skip, ``None`` — unknown (defer to config).
    """
    if compatible is None:
        return None
    label = evaluate_rules(compatible, ctx)
    if label == "TRUE":
        return True
    if label == "FALSE":
        return False
    if label == "UNKNOWN":
        return None
    return None


# ---------------------------------------------------------------------------
# RuleContext — typed context for script/driver rule evaluation
# ---------------------------------------------------------------------------


class RuleContext(TypedDict, total=False):
    """Context passed to :class:`Rule` and :class:`RuleEvaluator` callables."""

    script_name: str
    system_info: StaticSystemInfo | None
    config: ArgusConfig | None


@dataclass
class EvaluationResult:
    """Result of evaluating a collection of rules."""

    passed: bool
    reason: str = ""


class Rule(ABC):
    """A single compatibility rule evaluated against a :class:`RuleContext`."""

    @abstractmethod
    def __call__(self, ctx: RuleContext) -> bool:
        """Return ``True`` if the rule passes for the given context."""


class RuleEvaluator(ABC):
    """Evaluates a set of :class:`Rule` objects against a :class:`RuleContext`."""

    @abstractmethod
    def evaluate(self, rules: list[Rule], ctx: RuleContext) -> EvaluationResult:
        """Evaluate all *rules* and return the aggregated result."""


class RuleCondition(ABC):
    """Evaluates a declarative rule string against a :class:`RuleContext`."""

    @abstractmethod
    def evaluate(self, rule_str: str, ctx: RuleContext) -> bool:
        """Return ``True`` if *rule_str* matches *ctx*."""


def evaluate_rule(rule_str: str, context: dict[str, object]) -> bool:
    """Evaluate a single declarative rule string against a plain dict context.

    This is a lightweight entry point for ad-hoc evaluation outside the
    :class:`CompatContext` / :class:`RuleContext` machinery.
    """
    m = _RULE_RE.match(rule_str)
    if not m:
        return False
    expr = m.group("expr")
    tokens = _AND_OR_RE.split(expr.strip())
    result: bool | None = None
    expect_and = True

    for token in tokens:
        token = token.strip()
        if token == "AND":
            expect_and = True
            continue
        if token == "OR":
            expect_and = False
            continue

        cm = _COMP_RE.match(token)
        if not cm:
            return False

        ident = cm.group("ident")
        op = cm.group("op")
        raw_value = cm.group("value")
        expected = raw_value[1:-1]
        actual = context.get(ident)
        if actual is None:
            return False

        op_key = _OPERATORS[op]
        comp_result: bool
        if op_key == "eq":
            comp_result = str(actual) == expected
        elif op_key == "ne":
            comp_result = str(actual) != expected
        elif op_key == "gt":
            comp_result = str(actual) > expected
        elif op_key == "lt":
            comp_result = str(actual) < expected
        elif op_key == "ge":
            comp_result = str(actual) >= expected
        elif op_key == "le":
            comp_result = str(actual) <= expected
        elif op_key == "like":
            comp_result = fnmatch.fnmatch(str(actual), expected)
        elif op_key == "startswith":
            comp_result = str(actual).startswith(expected)
        elif op_key == "endswith":
            comp_result = str(actual).endswith(expected)
        else:
            return False

        if result is None:
            result = comp_result
        elif expect_and:
            result = result and comp_result
        else:
            result = result or comp_result

    return bool(result)
