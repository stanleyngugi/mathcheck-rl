"""Actual tensor/autograd controls for the optional local training integration."""
import pytest

torch = pytest.importorskip("torch")
from native_verify.grpo import LocalTrainingConfig, grpo_loss, state_digest


def test_gradient_rewards_good_completion_and_ignores_padding():
    logp = torch.zeros((3, 3), requires_grad=True)
    mask = torch.tensor([[True, True, False]]*3)
    old = torch.zeros_like(logp, requires_grad=True)
    reference = torch.zeros_like(logp, requires_grad=True)
    loss = grpo_loss(logp, old, reference, mask, torch.tensor([1., 0., 0.]), beta=0.01)
    loss.backward()
    assert (logp.grad[0, :2] < 0).all()
    assert (logp.grad[1:, :2] > 0).all()
    assert not logp.grad[:, 2].any()
    assert old.grad is None and reference.grad is None


def test_degenerate_groups_do_not_create_fake_training_updates():
    logp = torch.zeros((3, 2), requires_grad=True)
    for reward in (0., 1.):
        assert grpo_loss(logp, logp.detach(), logp.detach(), torch.ones_like(logp, dtype=torch.bool),
                         torch.full((3,), reward), beta=0.01) is None
    assert logp.grad is None


def test_masked_nonfinite_values_do_not_poison_valid_objective():
    current = torch.tensor([[0., float("nan")]]*3, requires_grad=True)
    mask = torch.tensor([[True, False]]*3)
    loss = grpo_loss(current, current.detach(), current.detach(), mask,
                     torch.tensor([1., 0., 0.]), beta=0.)
    assert torch.isfinite(loss)
    loss.backward()
    assert torch.isfinite(current.grad).all()


def test_real_optimizer_changes_policy_and_preserves_reference():
    model = torch.nn.Embedding(1, 3)
    reference = torch.nn.Embedding(1, 3)
    reference.load_state_dict(model.state_dict())
    initial, ref_initial = state_digest(model), state_digest(reference)
    logits = model(torch.tensor([0])).squeeze(0)
    logp = logits.log_softmax(-1).unsqueeze(1)
    loss = grpo_loss(logp, logp.detach(), logp.detach(), torch.ones_like(logp, dtype=torch.bool),
                    torch.tensor([1., 0., 0.]), beta=0.01)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=0)
    optimizer.zero_grad(); loss.backward(); optimizer.step()
    assert state_digest(model) != initial
    assert state_digest(reference) == ref_initial
    assert model(torch.tensor([0])).softmax(-1)[0, 0] > reference(torch.tensor([0])).softmax(-1)[0, 0]


@pytest.mark.parametrize("changes", [{"temperature": .2}, {"top_p": .9},
 {"group_size": 2}, {"learning_rate": float("nan")}, {"weight_decay": .01}])
def test_unsupported_training_settings_fail_before_sampling(changes):
    with pytest.raises(ValueError):
        LocalTrainingConfig(**changes)


def test_transformers_checkpoint_round_trip_and_real_update(tmp_path):
    pytest.importorskip("transformers")
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from native_verify.grpo import TransformersPolicy, SampleBatch, checkpoint_digest
    vocab = {"[UNK]": 0, "[EOS]": 1, "good": 2, "bad": 3, "prompt": 4}
    tokenizer = Tokenizer(WordLevel(vocab, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    checkpoint = tmp_path / "initial"
    checkpoint.mkdir()
    GPT2LMHeadModel(GPT2Config(vocab_size=5, n_positions=32, n_embd=16, n_layer=1, n_head=2,
                              eos_token_id=1, bos_token_id=1)).save_pretrained(checkpoint)
    PreTrainedTokenizerFast(tokenizer_object=tokenizer, unk_token="[UNK]", eos_token="[EOS]",
                            pad_token="[EOS]").save_pretrained(checkpoint)
    policy = TransformersPolicy(checkpoint, LocalTrainingConfig(max_new_tokens=4, learning_rate=.01))
    initial = state_digest(policy.model)
    sampled = policy.sample("prompt", 3)
    assert len(sampled.texts) == 3 and sampled.completion_mask.any(dim=1).all()
    # Force known EOS/padding positions without relying on a random draw.
    original_generate = policy.model.generate
    policy.model.generate = lambda **kwargs: torch.tensor([
        [4, 2, 1, 1], [4, 1, 1, 1], [4, 2, 3, 2]])
    try:
        eos_batch = policy.sample("prompt", 3)
    finally:
        policy.model.generate = original_generate
    assert eos_batch.completion_mask.tolist() == [[True, True, False], [True, False, False], [True, True, True]]
    assert not eos_batch.old_log_probs.requires_grad
    assert not eos_batch.reference_log_probs.requires_grad
    # Fixed token controls avoid attributing random fixture samples to learning.
    ids = torch.tensor([[4, 2, 1, 1], [4, 3, 1, 1], [4, 3, 1, 1]])
    mask = torch.tensor([[True, True, False]]*3)
    attention = torch.tensor([[1, 1, 1, 0]]*3)
    with torch.no_grad():
        old = policy._log_probs(policy.model, ids, attention, 1)
        ref = policy._log_probs(policy.reference, ids, attention, 1)
    batch = SampleBatch(["good", "bad", "bad"], ids, attention, 1, mask, old, ref)
    skipped = policy.update(batch, [0., 0., 0.])
    assert not skipped["optimizer_step"] and state_digest(policy.model) == initial
    update = policy.update(batch, [1., 0., 0.])
    assert update["optimizer_step"] and state_digest(policy.model) != initial
    saved = policy.save(tmp_path/"final")
    assert saved["policy_changed"] and saved["optimizer_steps"] == 1
    assert saved["checkpoint_sha256"] == checkpoint_digest(tmp_path/"final")
    reloaded = TransformersPolicy(tmp_path/"final", policy.config)
    assert state_digest(reloaded.model) == saved["state_sha256"]
    assert state_digest(policy.reference) == policy.reference_state_digest
