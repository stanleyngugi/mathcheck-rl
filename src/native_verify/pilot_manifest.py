"""Fail-closed construction of the frozen M5 pilot manifest.

This module is deliberately offline.  It does not import a provider SDK, start
training, inspect another benchmark, or mutate quota state.  Its only output is
the caller-owned preregistration document.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

from .specification_tasks import (
    generate_specification_tasks,
    specification_to_dict,
)


PILOT_PROTOCOL = "native-verify-m5-bounded-spec-v1"
PILOT_FAMILIES = (
    "bounded_count",
    "bounded_sum",
    "bounded_minimum",
    "bounded_pair_count",
)
PILOT_SPLITS = (
    (
        "training",
        10,
        20260909,
        "96c8f1139a37f1acd9fec83f6e61a54b60f2b02fc4fed79a2150ad52a3df90bc",
        "training_only",
    ),
    (
        "primary_evaluation",
        20,
        20270909,
        "34148fde00892e68abac3997856ba49f9a003e8ac5547e95820af3555cdd1249",
        "evaluation_only",
    ),
    (
        "confirmatory",
        20,
        20280909,
        "e0a208362d56742c1703be5d5ac02dd30d38db757e9d2da24c1246d5fb7a9a28",
        "sealed_until_primary_analysis_final",
    ),
)
PILOT_BUDGETS = {
    "maximum_provider_calls": 300,
    "maximum_spend_usd": 20,
    "maximum_wall_clock_minutes": 60,
    "evaluation_attempts_per_task": 1,
    "maximum_training_attempts_per_task": 3,
    "automatic_retries": 0,
}
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class PilotRuntime:
    provider: str
    model_id_revision: str
    trainer_runtime_version: str
    temperature: float
    top_p: float
    token_limit: int
    currency_conversion_source: str


@dataclass(frozen=True, slots=True)
class PilotInputs:
    native_commit: str
    verifier_commit: str
    release_manifest_canonical_sha256: str
    benchmark_completion_reference: str


def _require_frozen_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value.strip().upper() == "UNSET":
        raise ValueError(f"{name} must be frozen before manifest creation")
    return value.strip()


def _validate_runtime(runtime: PilotRuntime) -> dict[str, Any]:
    provider = _require_frozen_text("provider", runtime.provider)
    model = _require_frozen_text("model_id_revision", runtime.model_id_revision)
    trainer = _require_frozen_text(
        "trainer_runtime_version", runtime.trainer_runtime_version
    )
    currency = _require_frozen_text(
        "currency_conversion_source", runtime.currency_conversion_source
    )
    if isinstance(runtime.temperature, bool) or not isinstance(
        runtime.temperature, (int, float)
    ) or runtime.temperature < 0:
        raise ValueError("temperature must be a nonnegative number")
    if isinstance(runtime.top_p, bool) or not isinstance(runtime.top_p, (int, float)):
        raise ValueError("top_p must be a number")
    if not 0 < runtime.top_p <= 1:
        raise ValueError("top_p must be greater than zero and at most one")
    if type(runtime.token_limit) is not int or runtime.token_limit < 1:
        raise ValueError("token_limit must be a positive integer")
    return {
        "provider": provider,
        "model_id_revision": model,
        "trainer_runtime_version": trainer,
        "temperature": runtime.temperature,
        "top_p": runtime.top_p,
        "token_limit": runtime.token_limit,
        "currency_conversion_source": currency,
    }


def _validate_inputs(inputs: PilotInputs) -> dict[str, str]:
    native_commit = inputs.native_commit.strip().lower()
    verifier_commit = inputs.verifier_commit.strip().lower()
    release_hash = inputs.release_manifest_canonical_sha256.strip().lower()
    if _COMMIT_RE.fullmatch(native_commit) is None:
        raise ValueError("native_commit must be a full lowercase Git commit")
    if _COMMIT_RE.fullmatch(verifier_commit) is None:
        raise ValueError("verifier_commit must be a full lowercase Git commit")
    if _SHA256_RE.fullmatch(release_hash) is None:
        raise ValueError(
            "release_manifest_canonical_sha256 must be a lowercase SHA-256 digest"
        )
    completion = _require_frozen_text(
        "benchmark_completion_reference", inputs.benchmark_completion_reference
    )
    return {
        "native_commit": native_commit,
        "verifier_commit": verifier_commit,
        "release_manifest_canonical_sha256": release_hash,
        "benchmark_completion_reference": completion,
    }


def _ordered_task_payload(per_family: int, seed: int) -> list[dict[str, Any]]:
    tasks = generate_specification_tasks(
        families=list(PILOT_FAMILIES), per_family=per_family, seed=seed
    )
    return [
        {
            "task_id": task.task_id,
            "family": task.family,
            "specification": specification_to_dict(task.specification),
            "specification_digest": task.specification_digest,
        }
        for task in tasks
    ]


def canonical_json_sha256(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_release_manifest(release_manifest: object) -> dict[str, Any]:
    if not isinstance(release_manifest, dict):
        raise ValueError("release manifest must be a JSON object")
    if release_manifest.get("schema_version") != 1:
        raise ValueError("unsupported release manifest schema")
    if release_manifest.get("lean_version") != "4.23.0":
        raise ValueError("M5 requires the release-gated Lean 4.23.0 toolchain")
    lean_hash = release_manifest.get("lean_binary_sha256")
    if not isinstance(lean_hash, str) or _SHA256_RE.fullmatch(lean_hash) is None:
        raise ValueError("release manifest has no valid Lean binary digest")
    wheels = release_manifest.get("wheels")
    if not isinstance(wheels, dict) or len(wheels) != 4:
        raise ValueError("release manifest must bind exactly four wheels")
    if any(
        not isinstance(name, str)
        or not isinstance(digest, str)
        or _SHA256_RE.fullmatch(digest) is None
        for name, digest in wheels.items()
    ):
        raise ValueError("release manifest contains an invalid wheel digest")
    return release_manifest


def build_pilot_manifest(
    runtime: PilotRuntime,
    inputs: PilotInputs,
    release_manifest: object,
) -> dict[str, Any]:
    """Return a complete, deterministic preregistration or fail closed."""
    checked_release = _validate_release_manifest(release_manifest)
    checked_inputs = _validate_inputs(inputs)
    if canonical_json_sha256(checked_release) != checked_inputs[
        "release_manifest_canonical_sha256"
    ]:
        raise ValueError("release manifest digest does not match the frozen input")

    split_records: dict[str, Any] = {}
    digest_sets: list[set[str]] = []
    for name, per_family, seed, expected_commitment, visibility in PILOT_SPLITS:
        tasks = _ordered_task_payload(per_family, seed)
        actual_commitment = canonical_json_sha256(tasks)
        if actual_commitment != expected_commitment:
            raise RuntimeError(f"frozen {name} split commitment changed")
        digests = {task["specification_digest"] for task in tasks}
        if len(digests) != len(tasks):
            raise RuntimeError(f"frozen {name} split contains duplicate specifications")
        if any(digests.intersection(previous) for previous in digest_sets):
            raise RuntimeError("frozen pilot splits are not pairwise disjoint")
        digest_sets.append(digests)
        split_records[name] = {
            "seed": seed,
            "per_family": per_family,
            "task_count": len(tasks),
            "ordered_commitment_sha256": actual_commitment,
            "visibility": visibility,
            "tasks": tasks,
        }

    return {
        "schema_version": 1,
        "status": "preregistered_not_started",
        "protocol": PILOT_PROTOCOL,
        "environment": "native-verify-spec",
        "families": list(PILOT_FAMILIES),
        "runtime": _validate_runtime(runtime),
        "inputs": checked_inputs,
        "budgets": dict(PILOT_BUDGETS),
        "splits": split_records,
        "integrity": {
            "candidate_can_replace_specification": False,
            "evaluation_fed_into_training": False,
            "all_attempts_must_be_durable": True,
            "operational_failure_reward": 0,
        },
    }
