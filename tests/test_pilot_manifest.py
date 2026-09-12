import hashlib
import json

import pytest

from native_verify.pilot_manifest import (
    PILOT_BUDGETS,
    PilotInputs,
    PilotRuntime,
    build_pilot_manifest,
)


def canonical_sha256(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@pytest.fixture
def release_manifest():
    return {
        "schema_version": 1,
        "lean_version": "4.23.0",
        "lean_binary_sha256": "a" * 64,
        "wheels": {
            "lean_kernel_verifier-0.3.2-py3-none-any.whl": "b" * 64,
            "native_verify-0.2.1-py3-none-any.whl": "c" * 64,
            "native_verify_seq-0.2.1-py3-none-any.whl": "d" * 64,
            "mathcheck_rl-0.1.1-py3-none-any.whl": "e" * 64,
        },
    }


def frozen_runtime(**changes):
    values = {
        "provider": "provider-name",
        "model_id_revision": "model-name@immutable-revision",
        "trainer_runtime_version": "trainer==1.2.3",
        "temperature": 0.2,
        "top_p": 0.95,
        "token_limit": 2048,
        "currency_conversion_source": "not-applicable; provider bills in USD",
    }
    values.update(changes)
    return PilotRuntime(**values)


def frozen_inputs(release_manifest, **changes):
    values = {
        "native_commit": "1" * 40,
        "verifier_commit": "2" * 40,
        "release_manifest_canonical_sha256": canonical_sha256(release_manifest),
        "benchmark_completion_reference": "owner-attestation-2026-09-11",
    }
    values.update(changes)
    return PilotInputs(**values)


def test_manifest_reproduces_protocol_and_contains_no_answer_keys(release_manifest):
    manifest = build_pilot_manifest(
        frozen_runtime(), frozen_inputs(release_manifest), release_manifest
    )
    assert manifest["status"] == "preregistered_not_started"
    assert manifest["budgets"] == PILOT_BUDGETS
    assert {
        name: split["task_count"] for name, split in manifest["splits"].items()
    } == {"training": 40, "primary_evaluation": 80, "confirmatory": 80}
    all_digests = []
    for split in manifest["splits"].values():
        assert canonical_sha256(split["tasks"]) == split["ordered_commitment_sha256"]
        for task in split["tasks"]:
            assert "answer" not in task
            assert "answer" not in task["specification"]
            all_digests.append(task["specification_digest"])
    assert len(all_digests) == len(set(all_digests)) == 200


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("provider", "UNSET"),
        ("model_id_revision", ""),
        ("trainer_runtime_version", "UNSET"),
        ("temperature", -0.1),
        ("top_p", 0),
        ("top_p", 1.1),
        ("token_limit", 0),
        ("currency_conversion_source", "UNSET"),
    ],
)
def test_manifest_rejects_unfrozen_or_invalid_runtime(
    release_manifest, field, value
):
    with pytest.raises(ValueError):
        build_pilot_manifest(
            frozen_runtime(**{field: value}),
            frozen_inputs(release_manifest),
            release_manifest,
        )


def test_manifest_rejects_mismatched_release_digest(release_manifest):
    with pytest.raises(ValueError, match="does not match"):
        build_pilot_manifest(
            frozen_runtime(),
            frozen_inputs(
                release_manifest, release_manifest_canonical_sha256="f" * 64
            ),
            release_manifest,
        )


def test_manifest_rejects_missing_benchmark_completion_reference(release_manifest):
    with pytest.raises(ValueError, match="benchmark_completion_reference"):
        build_pilot_manifest(
            frozen_runtime(),
            frozen_inputs(release_manifest, benchmark_completion_reference="UNSET"),
            release_manifest,
        )
