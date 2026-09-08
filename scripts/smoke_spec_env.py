"""Local no-provider smoke for the answer-key-free v0 reward adapter."""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "environments" / "native_verify_spec"))

from lean_kernel_verifier.specification import ProblemSpec
import native_verify_spec as environment


def completion(answer: int):
    return [{"role": "assistant", "content": f"```json\n{{\"answer\": {answer}}}\n```"}]


async def main() -> int:
    env = environment.load_environment(
        families="bounded_minimum",
        num_per_family=1,
        eval_num_per_family=1,
        seed=17,
        eval_seed=1017,
    )
    row = env.dataset[0]
    payload = json.loads(row["answer"])
    spec = ProblemSpec.from_dict(payload["specification"])
    correct = next(
        x for x in range(spec.start, spec.stop)
        if eval(spec.expression, {"__builtins__": {}}, {"x": x})
    )
    states = ({}, {})
    accepted = await environment.specification_pass(completion(correct), row["answer"], states[0])
    rejected = await environment.specification_pass(completion(correct + 1), row["answer"], states[1])
    print(f"rows={len(env.dataset)} eval_rows={len(env.eval_dataset)}")
    print(f"correct_reward={accepted} wrong_reward={rejected}")
    print(f"status={states[0]['nv_spec_verdict'].status} scope={states[0]['nv_spec_verdict'].scope}")
    if accepted != 1.0 or rejected != 0.0:
        return 1
    print("answer-key-free env smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
