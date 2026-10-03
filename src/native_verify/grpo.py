"""Small local causal-LM GRPO integration; optional torch/transformers imports.

No reference answers enter this module. Rewards come from the caller's frozen
specification checker. This implements one original-GRPO update per sampled
three-completion group, with explicit sequence normalization and KL penalty.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class LocalTrainingConfig:
    seed: int = 20261003
    device: str = "cpu"
    learning_rate: float = 1e-5
    kl_coefficient: float = 0.01
    clip_epsilon: float = 0.2
    max_gradient_norm: float = 1.0
    weight_decay: float = 0.0
    group_size: int = 3
    max_new_tokens: int = 256
    temperature: float = 1.0
    top_p: float = 1.0
    precision: str = "float32"
    optimizer: str = "AdamW"
    tuning: str = "full"

    def __post_init__(self):
        for name in ("learning_rate", "kl_coefficient", "clip_epsilon",
                     "max_gradient_norm", "weight_decay", "temperature", "top_p"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.learning_rate <= 0 or self.kl_coefficient < 0 or self.weight_decay != 0:
            raise ValueError("positive learning rate, nonnegative KL and zero weight decay required")
        if not 0 < self.clip_epsilon < 1 or self.max_gradient_norm <= 0:
            raise ValueError("invalid clipping configuration")
        if self.group_size != 3 or type(self.group_size) is not int:
            raise ValueError("the pilot freezes three completions per group")
        if type(self.seed) is not int or not 0 <= self.seed < 2**63-5000 or type(self.max_new_tokens) is not int or self.max_new_tokens < 1:
            raise ValueError("integer seed and positive completion token limit required")
        if (self.precision, self.optimizer, self.tuning) != ("float32", "AdamW", "full"):
            raise ValueError("this driver freezes full float32 tuning with AdamW")
        # Avoid a mismatch between the sampled behavior distribution and the
        # policy log probabilities used by this deliberately small trainer.
        if self.temperature != 1 or self.top_p != 1:
            raise ValueError("this trainer freezes unbiased sampling at temperature=1, top_p=1")
        if self.device not in {"cpu", "cuda"}:
            raise ValueError("device must be cpu or cuda")


def grpo_loss(log_probs, old_log_probs, reference_log_probs, mask, rewards,
              *, beta: float, clip_epsilon: float = 0.2):
    """Original per-sequence GRPO reduction with population group std.

    Returns None for a degenerate binary reward group. Masked tokens carry no
    objective or gradient. Old and reference probabilities never carry gradients.
    """
    import torch
    if log_probs.ndim != 2 or any(x.shape != log_probs.shape for x in
                                    (old_log_probs, reference_log_probs, mask)):
        raise ValueError("log-probability and mask shapes must agree")
    if rewards.shape != (log_probs.shape[0],) or log_probs.shape[0] != 3:
        raise ValueError("one binary reward is required for each of three completions")
    if not torch.isfinite(rewards).all() or not ((rewards == 0) | (rewards == 1)).all():
        raise ValueError("rewards must be finite binary specification verdicts")
    if mask.dtype != torch.bool or not mask.any(dim=1).all():
        raise ValueError("each completion must contain at least one scored token")
    if not math.isfinite(beta) or beta < 0 or not 0 < clip_epsilon < 1:
        raise ValueError("invalid objective settings")
    std = rewards.std(unbiased=False)
    if std.item() == 0:
        return None
    advantages = ((rewards - rewards.mean()) / std).detach().unsqueeze(1)
    # Zero masked values *before* exponentiation so padding cannot introduce
    # NaNs or infinities into otherwise valid completion objectives.
    current = torch.where(mask, log_probs, torch.zeros_like(log_probs))
    old = torch.where(mask, old_log_probs.detach(), torch.zeros_like(log_probs))
    reference = torch.where(mask, reference_log_probs.detach(), torch.zeros_like(log_probs))
    ratio = (current - old).exp()
    surrogate = torch.minimum(ratio * advantages,
                              ratio.clamp(1-clip_epsilon, 1+clip_epsilon) * advantages)
    difference = reference - current
    kl = difference.exp() - difference - 1
    objective = torch.where(mask, surrogate - beta * kl, torch.zeros_like(current))
    loss = -(objective.sum(dim=1) / mask.sum(dim=1)).mean()
    if not torch.isfinite(loss):
        raise ValueError("nonfinite GRPO objective")
    return loss


def state_digest(model) -> str:
    """Digest exact named tensor bytes, independent of serialization timestamps."""
    import torch
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode() + b"\0")
        digest.update(str(tensor.dtype).encode() + b"\0")
        digest.update(str(tuple(tensor.shape)).encode() + b"\0")
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def checkpoint_digest(root: Path) -> str:
    """Bind all files in the local model/tokenizer bundle; reject symlink escapes."""
    root = root.resolve(strict=True)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or not any(p.suffix == ".safetensors" for p in files):
        raise ValueError("local checkpoint must contain safetensors model weights")
    digest = hashlib.sha256()
    for path in files:
        if root not in path.resolve().parents:
            raise ValueError("checkpoint symlink points outside its frozen bundle")
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024*1024), b""):
                digest.update(block)
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(slots=True)
class SampleBatch:
    texts: list[str]
    input_ids: Any
    attention_mask: Any
    prompt_length: int
    completion_mask: Any
    old_log_probs: Any
    reference_log_probs: Any


class TransformersPolicy:
    """Local safetensors checkpoint, fresh completion sampling and real AdamW updates."""

    def __init__(self, checkpoint: Path, config: LocalTrainingConfig):
        import copy
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.config = config
        self.initial_checkpoint_digest = checkpoint_digest(checkpoint)
        torch.manual_seed(config.seed)
        self.model = AutoModelForCausalLM.from_pretrained(
            str(checkpoint), local_files_only=True, trust_remote_code=False,
            use_safetensors=True, attn_implementation="eager",
            dtype=torch.float32,
        ).to(config.device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(checkpoint), local_files_only=True, trust_remote_code=False,
        )
        if self.tokenizer.eos_token_id is None:
            raise ValueError("tokenizer must define an end-of-sequence token")
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.reference = copy.deepcopy(self.model).eval()
        for parameter in self.reference.parameters():
            parameter.requires_grad_(False)
        self.model.eval()  # Disable dropout while retaining gradients.
        self.optimizer = torch.optim.AdamW(self.model.parameters(),
                           lr=config.learning_rate, weight_decay=config.weight_decay)
        self.initial_state_digest = state_digest(self.model)
        self.reference_state_digest = state_digest(self.reference)
        self.optimizer_steps = 0

    def set_sampling_seed(self, seed: int):
        import torch
        torch.manual_seed(seed)

    @staticmethod
    def _log_probs(model, ids, attention, prompt_length):
        import torch
        logits = model(input_ids=ids, attention_mask=attention).logits
        logits = logits[:, prompt_length-1:-1, :].float()
        labels = ids[:, prompt_length:]
        return torch.log_softmax(logits, dim=-1).gather(-1, labels.unsqueeze(-1)).squeeze(-1)

    def sample(self, prompt: str, count: int) -> SampleBatch:
        import torch
        from transformers import GenerationConfig
        if count not in (1, self.config.group_size):
            raise ValueError("only a single evaluation or one training group is permitted")
        if getattr(self.tokenizer, "chat_template", None):
            prompt = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
        encoded = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        ids = encoded["input_ids"].to(self.config.device)
        length = ids.shape[1]
        if length == 0:
            raise ValueError("prompt must contain at least one token")
        context_limit = getattr(self.model.config, "max_position_embeddings", None)
        if context_limit is not None and length + self.config.max_new_tokens > context_limit:
            raise ValueError("prompt plus frozen completion limit exceeds model context")
        with torch.no_grad():
            sequences = self.model.generate(
                input_ids=ids, attention_mask=encoded["attention_mask"].to(self.config.device),
                # Do not inherit checkpoint-specific sampling processors, which
                # would change the behavior distribution used by the objective.
                generation_config=GenerationConfig(
                    do_sample=True, temperature=1.0, top_p=1.0, top_k=0,
                    max_new_tokens=self.config.max_new_tokens, num_return_sequences=count,
                    pad_token_id=self.tokenizer.pad_token_id, eos_token_id=self.tokenizer.eos_token_id,
                ),
            )
        generated = sequences[:, length:]
        if generated.shape[1] == 0:
            raise ValueError("model produced no completion tokens")
        # Score through the first EOS, but exclude subsequent padding even when
        # PAD and EOS share an ID. Exactly one EOS is included in the objective.
        eos = generated.eq(self.tokenizer.eos_token_id)
        mask = (eos.cumsum(dim=1) - eos.to(torch.int64)) == 0
        attention = torch.cat((encoded["attention_mask"].to(self.config.device).repeat(count, 1),
                               mask.to(torch.int64)), dim=1)
        texts = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
        with torch.no_grad():
            old = self._log_probs(self.model, sequences, attention, length)
            reference = self._log_probs(self.reference, sequences, attention, length)
        return SampleBatch(texts, sequences, attention, length, mask, old, reference)

    def update(self, batch: SampleBatch, rewards: list[float]) -> dict[str, Any]:
        import torch
        if len(rewards) != self.config.group_size or len(batch.texts) != self.config.group_size:
            raise ValueError("training requires the frozen three-completion group")
        if len(set(rewards)) == 1:
            if rewards[0] not in (0.0, 1.0):
                raise ValueError("invalid binary reward")
            return {"optimizer_step": False, "reason": "zero_reward_variance"}
        log_probs = self._log_probs(self.model, batch.input_ids, batch.attention_mask,
                                    batch.prompt_length)
        loss = grpo_loss(log_probs, batch.old_log_probs, batch.reference_log_probs,
                         batch.completion_mask, torch.tensor(rewards, device=self.config.device),
                         beta=self.config.kl_coefficient, clip_epsilon=self.config.clip_epsilon)
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_gradient_norm,
                                             error_if_nonfinite=True)
        self.optimizer.step()
        self.optimizer_steps += 1
        return {"optimizer_step": True, "loss": loss.item(), "gradient_norm": norm.item(),
                "optimizer_steps_total": self.optimizer_steps}

    def save(self, directory: Path) -> dict[str, Any]:
        directory.mkdir(exist_ok=False)
        self.model.save_pretrained(directory, safe_serialization=True)
        self.tokenizer.save_pretrained(directory)
        for path in directory.rglob("*"):
            if path.is_file():
                with path.open("rb") as saved:
                    os.fsync(saved.fileno())
        current = state_digest(self.model)
        if state_digest(self.reference) != self.reference_state_digest:
            raise RuntimeError("frozen reference policy changed")
        return {"checkpoint_sha256": checkpoint_digest(directory), "state_sha256": current,
                "policy_changed": current != self.initial_state_digest,
                "optimizer_steps": self.optimizer_steps}
