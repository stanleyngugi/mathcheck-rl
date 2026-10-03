import hashlib

import pytest
from native_verify.dataset_import import build_import_manifest, task_from_import_record, text_sha256
from native_verify.reference_checks import reference_result


def question(split="train", index=0, text="There are 8 bags of 3 apples. How many apples?"):
    return dict(dataset="openai/gsm8k", revision="a"*40, source_split=split,
                source_index=index, source_id=f"GSM8K:{split}:{index}", question=text,
                question_sha256=text_sha256(text), source_file_sha256="b"*64)


def review(row, expression="8*3"):
    return dict(source_id=row["source_id"], question_sha256=row["question_sha256"],
                specification={"kind": "evaluate", "expression": expression},
                reviewer="question-only reviewer", review_context="separate formalization context",
                rationale="Eight bags, each containing three apples; multiplication.",
                answer_blind_construction=True, fidelity_review_passed=True)


def test_reward_contract_contains_no_reference_candidate():
    row = question()
    manifest = build_import_manifest([row], [review(row)], role="development")
    assert manifest["contains_expected_answers"] is False
    task = task_from_import_record(manifest["tasks"][0])
    assert reference_result(task.specification) == 24
    assert task.prompt.startswith(row["question"])
    assert set(manifest["tasks"][0]["specification"]) == {"kind", "expression", "start", "stop"}


@pytest.mark.parametrize("field", ["answer", "solution", "gold_answer", "expected"])
def test_source_solution_fields_are_rejected(field):
    row = question()
    row[field] = "24"
    with pytest.raises(ValueError, match="solution fields"):
        build_import_manifest([row], [review(row)], role="development")


def test_missing_review_false_blindness_and_disguised_constant_are_rejected():
    row = question()
    for decisions in ([], [review(row, "24")], [{**review(row), "answer_blind_construction": False}]):
        with pytest.raises(ValueError):
            build_import_manifest([row], decisions, role="development")


def test_official_test_cannot_be_imported_as_training():
    row = question("test")
    with pytest.raises(ValueError, match="role"):
        build_import_manifest([row], [review(row)], role="training")


def test_overlap_and_question_mutation_fail_before_freezing():
    row = question()
    spec_digest = build_import_manifest([row], [review(row)], role="training")["tasks"][0]["specification_digest"]
    with pytest.raises(ValueError, match="excluded specification"):
        build_import_manifest([row], [review(row)], role="development", excluded_specification_digests={spec_digest})
    with pytest.raises(ValueError, match="excluded question"):
        build_import_manifest([row], [review(row)], role="development", excluded_question_digests={row["question_sha256"]})
    changed = {**row, "question": "There are nine bags."}
    with pytest.raises(ValueError, match="digest"):
        build_import_manifest([changed], [review(row)], role="development")


def test_explicit_exclusion_is_not_a_solver_failure():
    row = question(text="Prove an unbounded theorem.")
    decision = dict(source_id=row["source_id"], question_sha256=row["question_sha256"],
                    exclusion_reason="Unbounded proof task outside the current DSL")
    manifest = build_import_manifest([row], [decision], role="development")
    assert not manifest["tasks"]
    assert len(manifest["exclusions"]) == 1


def test_duplicate_specifications_and_mixed_source_revisions_are_rejected():
    first, second = question(), question(index=1, text="Eight baskets each hold three apples. Total?")
    with pytest.raises(ValueError, match="duplicate.*specification"):
        build_import_manifest([first, second], [review(first), review(second)], role="development")
    second["revision"] = "c"*40
    with pytest.raises(ValueError, match="one frozen source"):
        build_import_manifest([first, second], [review(first), review(second)], role="development")


def test_imported_prompt_and_spec_mutations_cannot_reuse_frozen_record():
    row = question()
    record = build_import_manifest([row], [review(row)], role="development")["tasks"][0]
    with pytest.raises(ValueError, match="prompt"):
        task_from_import_record({**record, "prompt": "Answer an easier question."})
    with pytest.raises(ValueError, match="specification digest"):
        task_from_import_record({**record, "specification": {"kind": "evaluate", "expression": "8*4"}})
