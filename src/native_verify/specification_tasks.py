"""Answer-key-free bounded tasks backed by environment-owned specifications.

The model supplies only an integer candidate or a complete pair certificate.
It cannot replace or weaken the specification used for reward.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random
import re
import time
from typing import Any

from lean_kernel_verifier.certificates import (
    PairCertificate,
    PairCountSpec,
    verify_pair_certificate,
)
from lean_kernel_verifier.runner.checker_runner import CheckerRunConfig, LeanCheckerRunner
from lean_kernel_verifier.specification import ProblemSpec, verify_answer

from .runner import PINNED_LEAN_VERSION, locate_lean
from .types import Verdict

Specification = ProblemSpec | PairCountSpec
SCALAR_FAMILIES = ("bounded_count", "bounded_sum", "bounded_minimum")
SPECIFICATION_FAMILIES = (*SCALAR_FAMILIES, "bounded_pair_count")
_JSON_FENCE_RE = re.compile(r"\s*```json\s*\n(?P<body>.*?)```\s*", re.DOTALL)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class SpecificationTask:
    task_id: str
    family: str
    difficulty: str
    prompt: str
    specification: Specification

    @property
    def specification_digest(self) -> str:
        return self.specification.digest


def _submission_instructions(pair: bool) -> str:
    shape = (
        '{"answer": <count>, "pairs": [[x1, y1], ...]}'
        if pair else '{"answer": <nonnegative integer>}'
    )
    suffix = (
        "Pairs must be the complete satisfying relation, sorted lexicographically "
        "with no duplicates."
        if pair else
        "The candidate is checked by computation against the full stated bounded specification."
    )
    return (
        f" Submit exactly one fenced JSON object of the form `{shape}`. {suffix} "
        "Do not include or alter the checker specification."
    )


def _prompt(spec: Specification) -> str:
    if isinstance(spec, PairCountSpec):
        statement = (
            f"For integer pairs (x, y) with {spec.x_start} <= x < {spec.x_stop} and "
            f"{spec.y_start} <= y < {spec.y_stop}, list every pair satisfying "
            f"`{spec.expression}` and give the count."
        )
        return statement + _submission_instructions(True)
    if spec.kind == "count":
        statement = (
            f"How many integers x with {spec.start} <= x < {spec.stop} satisfy "
            f"`{spec.expression}`?"
        )
    elif spec.kind == "sum":
        statement = (
            f"Compute the exact sum of `{spec.expression}` over every integer x with "
            f"{spec.start} <= x < {spec.stop}."
        )
    elif spec.kind == "minimum":
        statement = (
            f"Find the least integer x with {spec.start} <= x < {spec.stop} satisfying "
            f"`{spec.expression}`."
        )
    else:
        statement = f"Compute the exact integer value of `{spec.expression}`."
    return statement + _submission_instructions(False)


def generate_specification_tasks(
    families: list[str] | None = None,
    per_family: int = 2,
    seed: int = 0,
) -> list[SpecificationTask]:
    if type(per_family) is not int or per_family < 1:
        raise ValueError("per_family must be a positive integer")
    selected = list(families or SPECIFICATION_FAMILIES)
    unknown = set(selected) - set(SPECIFICATION_FAMILIES)
    if unknown:
        raise ValueError(f"unknown specification families: {sorted(unknown)}")
    tasks: list[SpecificationTask] = []
    for family in selected:
        rng = random.Random(f"spec-v1:{seed}:{family}")
        seen: set[str] = set()
        attempts = 0
        while len(seen) < per_family:
            attempts += 1
            if attempts > 10000:
                raise RuntimeError(f"unable to generate {per_family} unique {family} tasks")
            spec = _generate_specification(family, rng)
            if spec.digest in seen:
                continue
            seen.add(spec.digest)
            tasks.append(SpecificationTask(
                task_id=f"spec_{family}_{spec.digest[:12]}",
                family=family,
                difficulty="bounded",
                prompt=_prompt(spec),
                specification=spec,
            ))
    return tasks


def generate_disjoint_specification_splits(
    *,
    families: list[str] | None = None,
    train_per_family: int = 2,
    eval_per_family: int = 1,
    train_seed: int = 0,
    eval_seed: int = 1000,
) -> tuple[list[SpecificationTask], list[SpecificationTask]]:
    train = generate_specification_tasks(families, train_per_family, train_seed)
    excluded = {task.specification_digest for task in train}
    selected = list(families or SPECIFICATION_FAMILIES)
    evaluation: list[SpecificationTask] = []
    attempt = 0
    while any(sum(t.family == family for t in evaluation) < eval_per_family for family in selected):
        if attempt >= 1000:
            raise RuntimeError("unable to construct a disjoint specification split")
        for task in generate_specification_tasks(selected, 1, eval_seed + attempt):
            if task.specification_digest in excluded:
                continue
            if sum(t.family == task.family for t in evaluation) >= eval_per_family:
                continue
            excluded.add(task.specification_digest)
            evaluation.append(task)
        attempt += 1
    return train, evaluation


def _generate_specification(family: str, rng: random.Random) -> Specification:
    if family == "bounded_count":
        start = rng.randrange(0, 20)
        stop = start + rng.randrange(20, 80)
        divisor = rng.randrange(2, 10)
        residue = rng.randrange(divisor)
        excluded = rng.randrange(2, 8)
        return ProblemSpec(
            "count", f"x%{divisor} == {residue} and x%{excluded} != 0", start, stop
        )
    if family == "bounded_sum":
        start = rng.randrange(0, 10)
        stop = start + rng.randrange(8, 30)
        coefficient = rng.randrange(1, 8)
        offset = rng.randrange(0, 20)
        return ProblemSpec("sum", f"x*x + {coefficient}*x + {offset}", start, stop)
    if family == "bounded_minimum":
        start = rng.randrange(0, 10)
        first = rng.randrange(3, 10)
        second = rng.randrange(3, 10)
        witness = rng.randrange(start, start + 30)
        stop = witness + rng.randrange(30, 100)
        return ProblemSpec(
            "minimum",
            f"x%{first} == {witness % first} and x%{second} == {witness % second}",
            start,
            stop,
        )
    if family == "bounded_pair_count":
        width = rng.randrange(5, 13)
        x_start = rng.randrange(0, 8)
        y_start = rng.randrange(0, 8)
        divisor = rng.randrange(2, 7)
        residue = rng.randrange(divisor)
        return PairCountSpec(
            f"x < y and (x+y)%{divisor} == {residue}",
            x_start,
            x_start + width,
            y_start,
            y_start + width,
        )
    raise ValueError(f"unknown specification family: {family}")


def parse_specification_submission(
    response_text: str, specification: Specification
) -> int | PairCertificate:
    if not isinstance(response_text, str) or len(response_text) > 100_000:
        raise ValueError("submission must be a string of at most 100000 characters")
    match = _JSON_FENCE_RE.fullmatch(response_text)
    if match is None:
        raise ValueError("submit exactly one fenced json object and no other text")
    try:
        payload = json.loads(
            match.group("body"), object_pairs_hook=_unique_json_object
        )
    except json.JSONDecodeError as exc:
        raise ValueError("submission contains invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("submission JSON must be an object")
    if isinstance(specification, PairCountSpec):
        if set(payload) != {"answer", "pairs"} or not isinstance(payload["pairs"], list):
            raise ValueError("pair submission requires exactly answer and pairs")
        try:
            pairs = tuple(tuple(pair) for pair in payload["pairs"])
        except TypeError as exc:
            raise ValueError("pairs must be a JSON array of two-element arrays") from exc
        return PairCertificate(pairs, payload["answer"])
    if set(payload) != {"answer"}:
        raise ValueError("scalar submission requires exactly answer")
    answer = payload["answer"]
    if type(answer) is not int or not 0 <= answer < 10**1000:
        raise ValueError("answer must be a nonnegative integer smaller than 10**1000")
    return answer


def verify_specification_submission(
    response_text: str,
    task: SpecificationTask,
    *,
    lean_bin: str | None = None,
    timeout_seconds: float = 120.0,
) -> Verdict:
    started = time.perf_counter()
    try:
        candidate = parse_specification_submission(response_text, task.specification)
    except (TypeError, ValueError) as exc:
        return Verdict(
            False, "parse", str(exc), duration_ms=_elapsed_ms(started), backend="none",
            status="invalid_input", scope="encoded_specification_only",
            specification_digest=task.specification_digest,
            artifact_digest=_submission_digest(response_text),
        )
    backend = locate_lean(lean_bin, probe=False)
    if backend is None:
        return Verdict(
            False, "internal", "isolated_lean_not_configured",
            duration_ms=_elapsed_ms(started), backend="none", status="operational_error",
            scope="encoded_specification_only",
            specification_digest=task.specification_digest,
            artifact_digest=_submission_digest(response_text),
        )
    runner = LeanCheckerRunner(CheckerRunConfig(
        lean_executable=backend.executable,
        timeout_seconds=max(1, int(timeout_seconds)),
        min_lean_version=PINNED_LEAN_VERSION,
        required_lean_version=PINNED_LEAN_VERSION,
        execution_mode="oneshot_cli",
    ))
    try:
        if isinstance(task.specification, PairCountSpec):
            assert isinstance(candidate, PairCertificate)
            result = verify_pair_certificate(task.specification, candidate, runner)
        else:
            assert isinstance(candidate, int)
            result = verify_answer(task.specification, candidate, runner)
    finally:
        runner.close()
    checker = result.checker
    if result.status == "checked_success":
        stage, reason = "verified", None
    elif result.status == "mathematical_rejection":
        stage, reason = "specification_check", "candidate_does_not_satisfy_specification"
    elif checker.timed_out:
        stage, reason = "timeout", "checker_timeout"
    else:
        stage, reason = "internal", "checker_backend_error"
    diagnostics = [
        line.strip()
        for line in (checker.stdout + "\n" + checker.stderr).splitlines()
        if line.strip()
    ][-10:]
    return Verdict(
        result.verified,
        stage,
        reason,
        diagnostics=diagnostics,
        duration_ms=_elapsed_ms(started),
        backend=checker.backend_mode,
        status=result.status,
        scope=result.scope,
        specification_digest=result.specification_digest,
        artifact_digest=_submission_digest(response_text),
        checker_invocations=1,
    )


def specification_to_dict(specification: Specification) -> dict[str, Any]:
    if isinstance(specification, PairCountSpec):
        return {
            "kind": specification.kind,
            "expression": specification.expression,
            "x_start": specification.x_start,
            "x_stop": specification.x_stop,
            "y_start": specification.y_start,
            "y_stop": specification.y_stop,
        }
    return {
        "kind": specification.kind,
        "expression": specification.expression,
        "start": specification.start,
        "stop": specification.stop,
    }


def specification_from_dict(data: dict[str, Any]) -> Specification:
    if not isinstance(data, dict):
        raise ValueError("specification must be an object")
    if data.get("kind") == "count_pairs":
        return PairCountSpec.from_dict(data)
    return ProblemSpec.from_dict(data)


def _submission_digest(response_text: object) -> str:
    if not isinstance(response_text, str):
        return ""
    return hashlib.sha256(response_text.encode("utf-8")).hexdigest()


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
