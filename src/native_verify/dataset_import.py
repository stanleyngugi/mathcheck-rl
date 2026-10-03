"""Offline, question-only dataset import with explicit reviewed contracts.

Review attestations are provenance, not a mechanical proof of prose fidelity.
The solving policy must receive the returned frozen task, never author its spec.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from lean_kernel_verifier.specification import ProblemSpec
from .specification_tasks import (
    SpecificationTask, _submission_instructions, specification_from_dict,
    specification_to_dict,
)

_FIELDS = {"dataset", "revision", "source_split", "source_index", "source_id",
           "question", "question_sha256", "source_file_sha256"}
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_ROLES = {"train": {"training", "development"},
          "test": {"held_out_test", "evaluation_demonstration"}}


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value.strip().upper() == "UNSET":
        raise ValueError(f"{name} must be recorded")
    return value


def _question(row: dict[str, Any]) -> None:
    if not isinstance(row, dict) or set(row) != _FIELDS:
        raise ValueError("question-only row has unexpected/missing fields; solution fields are forbidden")
    if row["dataset"] != "openai/gsm8k" or row["source_split"] not in _ROLES:
        raise ValueError("unsupported dataset or source split")
    if not isinstance(row["revision"], str) or not _COMMIT.fullmatch(row["revision"]):
        raise ValueError("source revision must be a full immutable Git commit")
    if type(row["source_index"]) is not int or row["source_index"] < 0:
        raise ValueError("source index must be a nonnegative integer")
    if row["source_id"] != f'GSM8K:{row["source_split"]}:{row["source_index"]}':
        raise ValueError("source identity does not match its split/index")
    question = _nonempty(row["question"], "question")
    if len(question) > 20000 or row["question_sha256"] != text_sha256(question):
        raise ValueError("question digest or size is invalid")
    if not isinstance(row["source_file_sha256"], str) or not _SHA256.fullmatch(row["source_file_sha256"]):
        raise ValueError("source file digest must be recorded")


def build_import_manifest(
    questions: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    *,
    role: str,
    excluded_question_digests: set[str] | None = None,
    excluded_specification_digests: set[str] | None = None,
) -> dict[str, Any]:
    if not questions:
        raise ValueError("import requires at least one question")
    excluded_questions = excluded_question_digests or set()
    excluded_specs = excluded_specification_digests or set()
    by_id = {}
    for decision in decisions:
        if not isinstance(decision, dict) or not isinstance(decision.get("source_id"), str):
            raise ValueError("every decision requires a source identity")
        if decision["source_id"] in by_id:
            raise ValueError("duplicate review decision")
        by_id[decision["source_id"]] = decision
    tasks, exclusions = [], []
    question_digests, spec_digests, source_ids = set(), set(), set()
    provenance = None
    for row in questions:
        _question(row)
        if role not in _ROLES[row["source_split"]]:
            raise ValueError("source split is incompatible with the requested experiment role")
        identity = (row["dataset"], row["revision"], row["source_split"], row["source_file_sha256"])
        if provenance is not None and identity != provenance:
            raise ValueError("one manifest must use one frozen source file")
        provenance = identity
        qdigest = row["question_sha256"]
        if qdigest in question_digests or qdigest in excluded_questions or row["source_id"] in source_ids:
            raise ValueError("duplicate or excluded question")
        question_digests.add(qdigest)
        source_ids.add(row["source_id"])
        decision = by_id.get(row["source_id"])
        if decision is None or decision.get("question_sha256") != qdigest:
            raise ValueError("every question needs a digest-bound review or explicit exclusion")
        if "exclusion_reason" in decision:
            if set(decision) != {"source_id", "question_sha256", "exclusion_reason"}:
                raise ValueError("invalid exclusion fields")
            exclusions.append({**row, "exclusion_reason": _nonempty(decision["exclusion_reason"], "exclusion reason")})
            continue
        required = {"source_id", "question_sha256", "specification", "reviewer",
                    "review_context", "rationale", "answer_blind_construction", "fidelity_review_passed"}
        if set(decision) != required or decision["answer_blind_construction"] is not True or decision["fidelity_review_passed"] is not True:
            raise ValueError("accepted specifications require an explicit answer-blind fidelity review")
        for field in ("reviewer", "review_context", "rationale"):
            _nonempty(decision[field], field)
        spec = specification_from_dict(decision["specification"])
        # The demonstration admits arithmetic derived from quantities in prose,
        # not a bare numeral masquerading as an evaluate specification.
        if isinstance(spec, ProblemSpec) and spec.kind == "evaluate":
            import ast
            if not any(isinstance(node, ast.BinOp) for node in ast.walk(ast.parse(spec.expression, mode="eval"))):
                raise ValueError("a bare constant is not an answer-blind arithmetic formalization")
        if spec.digest in spec_digests or spec.digest in excluded_specs:
            raise ValueError("duplicate or excluded specification")
        spec_digests.add(spec.digest)
        task = SpecificationTask(
            task_id=f'{row["source_id"]}:{spec.digest[:12]}', family=f"imported_{spec.kind}",
            difficulty="reviewed_dataset_slice", prompt=row["question"] + _submission_instructions(
                spec.kind == "count_pairs"), specification=spec,
        )
        tasks.append({**row, "task_id": task.task_id, "family": task.family,
                      "prompt": task.prompt, "specification": specification_to_dict(spec),
                      "specification_digest": spec.digest, "contains_expected_answer": False,
                      "review": {k: decision[k] for k in required - {"source_id", "question_sha256", "specification"}}})
    if set(by_id) != source_ids:
        raise ValueError("review file contains decisions outside the selected question slice")
    payload = {"schema": "mathcheck-gsm8k-import-v1", "status": "frozen_not_native_verified",
               "role": role, "questions_selected": len(questions), "tasks": tasks,
               "exclusions": exclusions, "contains_expected_answers": False,
               "fidelity": "review_attestation_not_formal_proof"}
    payload["manifest_sha256"] = text_sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload


def task_from_import_record(record: dict[str, Any]) -> SpecificationTask:
    if text_sha256(record["question"]) != record["question_sha256"]:
        raise ValueError("imported question digest changed")
    expected_prompt = record["question"] + _submission_instructions(record["specification"]["kind"] == "count_pairs")
    if record["prompt"] != expected_prompt or record["contains_expected_answer"] is not False:
        raise ValueError("imported prompt or answer-key flag changed")
    spec = specification_from_dict(record["specification"])
    if spec.digest != record["specification_digest"]:
        raise ValueError("imported specification digest changed")
    return SpecificationTask(record["task_id"], record["family"], "reviewed_dataset_slice",
                             record["prompt"], spec)
