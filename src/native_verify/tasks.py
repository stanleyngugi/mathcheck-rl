from __future__ import annotations

import random
import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class Task:
    task_id: str
    family: str
    difficulty: str
    prompt: str
    train_values: list[int]
    holdout_values: list[int]
    reference_artifact: str
    metadata: dict = field(default_factory=dict)


def _rule_prompt(statement: str, values: list[int], shown: int) -> str:
    listed = ", ".join(f"a({i})={v}" for i, v in enumerate(values[:shown]))
    return (
        f"{statement}\n\n"
        f"Reference values: {listed}.\n"
        "Submit a Lean 4 definition `def f (n : Nat) : Nat` intended to compute a(n). "
        f"Reward checks every index 0 <= n < {len(values)}; the unlisted suffix is hidden. "
        "Passing establishes only agreement on that finite observation range. Respond with "
        "a single ```lean code block containing pure definitions only: no imports, no "
        "attributes, no theorems."
    )


def _modpow_ref(base: int, modulus: int) -> str:
    return (
        "def powMod (base exp mod : Nat) : Nat :=\n"
        "  if mod == 0 then 0\n"
        "  else if mod == 1 then 0\n"
        "  else\n"
        "    let rec loop (b e acc fuel : Nat) : Nat :=\n"
        "      match fuel with\n"
        "      | 0 => acc\n"
        "      | fuel' + 1 =>\n"
        "          if e == 0 then acc\n"
        "          else\n"
        "            let acc' := if e % 2 == 1 then (acc * b) % mod else acc\n"
        "            loop ((b * b) % mod) (e / 2) acc' fuel'\n"
        "    loop (base % mod) exp 1 (exp + 1)\n"
        "\n"
        f"def f (n : Nat) : Nat := powMod {base} n {modulus}"
    )


def _digit_sum_ref() -> str:
    return (
        "def digitSum (n : Nat) : Nat :=\n"
        "  let rec loop (m acc fuel : Nat) : Nat :=\n"
        "    match fuel with\n"
        "    | 0 => acc\n"
        "    | fuel' + 1 =>\n"
        "        if m == 0 then acc\n"
        "        else loop (m / 10) (acc + m % 10) fuel'\n"
        "  loop n 0 (n + 1)\n"
        "\n"
        "def f (n : Nat) : Nat := digitSum n"
    )


def make_linear(rng: random.Random, index: int) -> Task:
    p = rng.randint(2, 9)
    q = rng.randint(0, 20)
    statement = (
        f"The sequence satisfies a(n) = {p}*n + {q} for all n >= 0."
    )
    total = [p * n + q for n in range(64)]
    return Task(
        task_id=f"linear_{index}",
        family="linear",
        difficulty="easy",
        prompt=_rule_prompt(statement, total, 10),
        train_values=total[:10],
        holdout_values=total[10:],
        reference_artifact=f"def f (n : Nat) : Nat := {p} * n + {q}",
        metadata={"p": p, "q": q},
    )


def make_polynomial(rng: random.Random, index: int) -> Task:
    c3 = rng.randint(0, 3)
    c2 = rng.randint(0, 6)
    c1 = rng.randint(1, 9)
    c0 = rng.randint(0, 15)

    def poly(n: int) -> int:
        return c3 * n**3 + c2 * n**2 + c1 * n + c0

    terms = []
    if c3:
        terms.append(f"{c3} * n * n * n")
    if c2:
        terms.append(f"{c2} * n * n")
    if c1:
        terms.append(f"{c1} * n")
    terms.append(str(c0))
    expr = " + ".join(terms)
    statement = f"The sequence satisfies a(n) = {expr} for all n >= 0."
    total = [poly(n) for n in range(48)]
    return Task(
        task_id=f"poly_{index}",
        family="explicit_polynomial",
        difficulty="medium",
        prompt=_rule_prompt(statement, total, 8),
        train_values=total[:8],
        holdout_values=total[8:],
        reference_artifact=f"def f (n : Nat) : Nat := {expr}",
        metadata={"c3": c3, "c2": c2, "c1": c1, "c0": c0},
    )


def make_closed_form_sum(rng: random.Random, index: int) -> Task:
    variant = rng.choice(["triangular", "sum_squares", "sum_cubes"])
    scale = rng.randint(1, 9)
    offset = rng.randint(0, 20)

    def triangular(n: int) -> int:
        return n * (n + 1) // 2

    def sum_squares(n: int) -> int:
        return n * (n + 1) * (2 * n + 1) // 6

    def sum_cubes(n: int) -> int:
        return (n * (n + 1) // 2) ** 2

    specs = {
        "triangular": (
            "a(n) is the sum 1 + 2 + ... + n (with a(0)=0)",
            triangular,
            "def f (n : Nat) : Nat := n * (n + 1) / 2",
        ),
        "sum_squares": (
            "a(n) is the sum of squares 1^2 + 2^2 + ... + n^2 (with a(0)=0)",
            sum_squares,
            "def f (n : Nat) : Nat := n * (n + 1) * (2 * n + 1) / 6",
        ),
        "sum_cubes": (
            "a(n) is the sum of cubes 1^3 + 2^3 + ... + n^3 (with a(0)=0)",
            sum_cubes,
            "def f (n : Nat) : Nat := (n * (n + 1) / 2) * (n * (n + 1) / 2)",
        ),
    }
    base_statement, fn, base_artifact = specs[variant]
    statement = f"a(n) is {scale} times ({base_statement}) plus {offset}."
    artifact_body = base_artifact.split(":=", 1)[1].strip()
    artifact = f"def f (n : Nat) : Nat := {scale} * ({artifact_body}) + {offset}"
    total = [scale * fn(n) + offset for n in range(48)]
    return Task(
        task_id=f"{variant}_{index}",
        family="closed_form_sum",
        difficulty="medium",
        prompt=_rule_prompt(statement, total, 8),
        train_values=total[:8],
        holdout_values=total[8:],
        reference_artifact=artifact,
        metadata={"variant": variant, "scale": scale, "offset": offset},
    )


def make_geometric_mod(rng: random.Random, index: int) -> Task:
    base = rng.randint(2, 7)
    modulus = rng.choice([13, 17, 19, 23, 29, 31])

    def gmod(n: int) -> int:
        return pow(base, n, modulus)

    statement = (
        f"a(n) is {base} raised to the power n, modulo {modulus} "
        f"(i.e., the remainder of {base}^n divided by {modulus})."
    )
    total = [gmod(n) for n in range(64)]
    return Task(
        task_id=f"gmod_{index}",
        family="geometric_mod",
        difficulty="hard",
        prompt=_rule_prompt(statement, total, 10),
        train_values=total[:10],
        holdout_values=total[10:],
        reference_artifact=_modpow_ref(base, modulus),
        metadata={"base": base, "modulus": modulus},
    )


def make_digit_sum(rng: random.Random, index: int) -> Task:
    offset = rng.randint(0, 999)
    def dsum(n: int) -> int:
        return sum(int(d) for d in str(n))

    statement = f"a(n) is the sum of the decimal digits of n + {offset}."
    total = [dsum(n + offset) for n in range(60)]
    return Task(
        task_id=f"dsum_{index}",
        family="digit_sum",
        difficulty="hard",
        prompt=_rule_prompt(statement, total, 12),
        train_values=total[:12],
        holdout_values=total[12:],
        reference_artifact=_digit_sum_ref().replace("digitSum n", f"digitSum (n + {offset})"),
        metadata={"offset": offset},
    )


FAMILIES: dict[str, Callable[[random.Random, int], Task]] = {
    "linear": make_linear,
    "explicit_polynomial": make_polynomial,
    "closed_form_sum": make_closed_form_sum,
    "geometric_mod": make_geometric_mod,
    "digit_sum": make_digit_sum,
}


def generate_tasks(
    families: list[str] | None = None,
    per_family: int = 4,
    seed: int = 0,
) -> list[Task]:
    selected = families or list(FAMILIES)
    unknown = set(selected) - set(FAMILIES)
    if unknown:
        raise ValueError(f"unknown families: {sorted(unknown)}")
    if type(per_family) is not int or per_family < 1:
        raise ValueError("per_family must be a positive integer")
    tasks: list[Task] = []
    for family in selected:
        rng = random.Random(f"{seed}:{family}")
        seen: set[str] = set()
        attempts = 0
        while len(seen) < per_family:
            attempts += 1
            if attempts > 10000:
                raise RuntimeError(f"unable to generate {per_family} unique {family} tasks")
            task = FAMILIES[family](rng, len(seen))
            digest = task_fingerprint(task)
            if digest in seen:
                continue
            seen.add(digest)
            task.task_id = f"{family}_{digest[:12]}"
            task.metadata["specification_digest"] = digest
            tasks.append(task)
    return tasks


def task_fingerprint(task: Task) -> str:
    payload = {
        "contract": "finite_observation_v1",
        "family": task.family,
        "metadata": {k: v for k, v in task.metadata.items() if k != "specification_digest"},
        "train": task.train_values,
        "holdout": task.holdout_values,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def generate_disjoint_task_splits(
    families: list[str] | None = None,
    *,
    train_per_family: int = 8,
    eval_per_family: int = 2,
    train_seed: int = 0,
    eval_seed: int = 1000,
) -> tuple[list[Task], list[Task]]:
    selected = list(families or FAMILIES)
    train = generate_tasks(selected, train_per_family, train_seed)
    excluded = {task_fingerprint(task) for task in train}
    evaluation: list[Task] = []
    attempt = 0
    while any(sum(t.family == family for t in evaluation) < eval_per_family for family in selected):
        if attempt >= 10000:
            raise RuntimeError("unable to construct a mathematically disjoint evaluation split")
        for task in generate_tasks(selected, 1, eval_seed + attempt):
            digest = task_fingerprint(task)
            if digest in excluded:
                continue
            if sum(t.family == task.family for t in evaluation) >= eval_per_family:
                continue
            excluded.add(digest)
            evaluation.append(task)
        attempt += 1
    return train, evaluation
