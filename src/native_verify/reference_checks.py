"""Independent Python controls for research QA; never used by the reward adapter.

This interpreter evaluates the restricted specification AST directly. It does
not call the Engine's Lean translator or execute arbitrary Python expressions.
Its outputs are derived control values, not reference labels stored in tasks.
"""
from __future__ import annotations

import ast
import operator

from lean_kernel_verifier.certificates import PairCertificate, PairCountSpec
from lean_kernel_verifier.specification import ProblemSpec

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
        ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge}


def _interpret(node: ast.AST, bindings: dict[str, int]):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.Name) and node.id in bindings:
        return bindings[node.id]
    if isinstance(node, ast.UnaryOp):
        value = _interpret(node.operand, bindings)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.Not):
            return not value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_interpret(node.left, bindings),
                                  _interpret(node.right, bindings))
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(_interpret(value, bindings) for value in node.values)
        if isinstance(node.op, ast.Or):
            return any(_interpret(value, bindings) for value in node.values)
    if isinstance(node, ast.Compare):
        left = _interpret(node.left, bindings)
        for op, right_node in zip(node.ops, node.comparators):
            right = _interpret(right_node, bindings)
            if type(op) not in _CMP or not _CMP[type(op)](left, right):
                return False
            left = right
        return True
    raise ValueError("unsupported reference AST")


def reference_result(spec: ProblemSpec | PairCountSpec) -> int | PairCertificate:
    """Compute a control result from an already validated immutable specification."""
    tree = ast.parse(spec.expression, mode="eval").body
    if isinstance(spec, PairCountSpec):
        pairs = tuple((x, y) for x in range(spec.x_start, spec.x_stop)
                      for y in range(spec.y_start, spec.y_stop)
                      if _interpret(tree, {"x": x, "y": y}))
        return PairCertificate(pairs, len(pairs))
    if spec.kind == "evaluate":
        return _interpret(tree, {})
    if spec.kind == "sum":
        return sum(_interpret(tree, {"x": x}) for x in range(spec.start, spec.stop))
    satisfying = [x for x in range(spec.start, spec.stop) if _interpret(tree, {"x": x})]
    if spec.kind == "count":
        return len(satisfying)
    if not satisfying:
        raise ValueError("minimum has no solution in its declared interval")
    return satisfying[0]


def reference_accepts(spec: ProblemSpec | PairCountSpec,
                      candidate: int | PairCertificate) -> bool:
    if isinstance(spec, PairCountSpec):
        return isinstance(candidate, PairCertificate) and candidate == reference_result(spec)
    if type(candidate) is not int or not 0 <= candidate < 10**1000:
        return False
    try:
        return candidate == reference_result(spec)
    except ValueError:
        return False
