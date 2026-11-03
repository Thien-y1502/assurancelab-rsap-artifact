from __future__ import annotations

import itertools
import random
import sys
from pathlib import Path
from statistics import median

BUNDLE_ROOT = Path(__file__).resolve().parents[1]
ROOT = BUNDLE_ROOT if (BUNDLE_ROOT / "src").exists() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(BUNDLE_ROOT))

from assurance_lab import AnytimeCertificate, AnytimeStatus  # noqa: E402
from common import environment_record, mean_ci, wilson, write_json, write_jsonl  # noqa: E402


SEEDS = (701, 809, 907, 1009, 1103)
EPISODES_PER_SEED = 1000
BUDGET = 80.0
ALPHA = 0.05
TAU_SAFE = 0.25
TAU_UNSAFE = 0.55
ACTIONS = (
    {"id": "a0", "cost": 1.0, "safe_loss": 0.10, "unsafe_loss": 0.65},
    {"id": "a1", "cost": 1.5, "safe_loss": 0.08, "unsafe_loss": 0.66},
    {"id": "a2", "cost": 2.0, "safe_loss": 0.15, "unsafe_loss": 0.64},
    {"id": "a3", "cost": 3.0, "safe_loss": 0.05, "unsafe_loss": 0.68},
    {"id": "a4", "cost": 4.0, "safe_loss": 0.12, "unsafe_loss": 0.67},
)


def choose_action(policy: str, step: int, counts: dict[str, int], losses: dict[str, int]) -> dict[str, float | str]:
    if policy == "uniform_eprocess":
        return ACTIONS[step % len(ACTIONS)]
    if policy == "risk_score_naive":
        return max(ACTIONS, key=lambda item: ((TAU_UNSAFE - item["safe_loss"]) / item["cost"], -item["cost"]))
    if policy == "greedy_cost":
        return min(ACTIONS, key=lambda item: (item["cost"], item["id"]))
    if policy == "random_eprocess":
        return ACTIONS[(step * 3 + 1) % len(ACTIONS)]
    if policy in {"rsap", "risk_score_eprocess"}:
        scores = []
        for action in ACTIONS:
            count = counts[action["id"]]
            observed = losses[action["id"]]
            posterior = (0.5 + observed) / (1.0 + count)
            optimistic = max(0.0, posterior - 0.05 / (1.0 + count) ** 0.5)
            score = (TAU_UNSAFE - optimistic) / action["cost"]
            scores.append((score, -action["cost"], action))
        return max(scores, key=lambda item: (item[0], item[1]))[2]
    raise ValueError(policy)


def run_episode(policy: str, uniforms: list[float], safe: bool, episode: int, *, budget: float, loss_shift: float = 0.0) -> dict[str, object]:
    certified = policy in {"uniform_eprocess", "random_eprocess", "rsap", "risk_score_eprocess"}
    certificate = AnytimeCertificate(
        claim_id=f"rsap-{policy}-{episode}",
        claim_version="2026-11-03-v2",
        tau_unsafe=TAU_UNSAFE,
        tau_safe=TAU_SAFE,
        alpha_pass=ALPHA,
        alpha_fail=ALPHA,
        lambda_pass=0.5,
        lambda_fail=0.5,
    ) if certified else None
    counts = {action["id"]: 0 for action in ACTIONS}
    losses = {action["id"]: 0 for action in ACTIONS}
    trace: list[dict[str, object]] = []
    cost = 0.0
    decision = "UNKNOWN"
    for step, uniform in enumerate(uniforms):
        action = choose_action(policy, step, counts, losses)
        if cost + float(action["cost"]) > budget:
            break
        probability = float(action["safe_loss"] if safe else action["unsafe_loss"]) + loss_shift
        probability = min(0.999, max(0.001, probability))
        loss = int(uniform < probability)
        counts[str(action["id"])] += 1
        losses[str(action["id"])] += loss
        cost += float(action["cost"])
        if certificate is not None:
            update = certificate.update_loss(loss, evidence_id=f"{policy}-{episode}-{step}")
            decision = update.status.value
            trace.append({"step": step, "action": action["id"], "loss": loss, "cost": cost, "status": decision, "pass_wealth": update.pass_wealth, "fail_wealth": update.fail_wealth})
            if update.status in {AnytimeStatus.PASS, AnytimeStatus.FAIL, AnytimeStatus.CONFLICT, AnytimeStatus.INVALID}:
                break
        else:
            trace.append({"step": step, "action": action["id"], "loss": loss, "cost": cost, "status": "RUNNING"})
            if len(trace) >= 5:
                recent = [int(item["loss"]) for item in trace[-5:]]
                if sum(recent) <= 1:
                    decision = "PASS"
                    break
                if sum(recent) >= 4:
                    decision = "FAIL"
                    break
    return {"policy": policy, "safe": safe, "episode": episode, "decision": decision, "cost": cost, "steps": len(trace), "trace": trace, "budget_ok": cost <= budget + 1e-12}


def proof_audit() -> dict[str, object]:
    disagreements = 0
    rows = 0
    for losses in itertools.product((0, 1), repeat=10):
        cert = AnytimeCertificate(claim_id="proof", claim_version="v2", tau_unsafe=TAU_UNSAFE, tau_safe=TAU_SAFE, alpha_pass=ALPHA, alpha_fail=ALPHA, lambda_pass=0.5, lambda_fail=0.5)
        pass_wealth = fail_wealth = 1.0
        for step, loss in enumerate(losses):
            update = cert.update_loss(loss, evidence_id=f"proof-{step}")
            pass_wealth *= 1.0 + 0.5 * (TAU_UNSAFE - loss)
            fail_wealth *= 1.0 + 0.5 * (loss - TAU_SAFE)
            rows += 1
            if abs(update.pass_wealth - pass_wealth) > 1e-12 or abs(update.fail_wealth - fail_wealth) > 1e-12:
                disagreements += 1
    expectation_checks = []
    for lam in (0.0, 0.25, 0.5, 0.75, 1.0):
        pass_at_tau = (1 - TAU_UNSAFE) * (1 + lam * TAU_UNSAFE) + TAU_UNSAFE * (1 + lam * (TAU_UNSAFE - 1))
        fail_at_tau = (1 - TAU_SAFE) * (1 + lam * (0 - TAU_SAFE)) + TAU_SAFE * (1 + lam * (1 - TAU_SAFE))
        expectation_checks.append({"lambda": lam, "pass_null_expectation": pass_at_tau, "fail_null_expectation": fail_at_tau})
    return {"enumerated_sequences": 2 ** 10, "wealth_rows": rows, "implementation_disagreements": disagreements, "expectation_checks": expectation_checks, "pass": disagreements == 0 and all(item["pass_null_expectation"] <= 1 + 1e-12 and item["fail_null_expectation"] <= 1 + 1e-12 for item in expectation_checks)}


def summarize(rows: list[dict[str, object]], policies: tuple[str, ...]) -> dict[str, object]:
    result: dict[str, object] = {}
    for policy in policies:
        current = [row for row in rows if row["policy"] == policy]
        safe_rows = [row for row in current if row["safe"]]
        unsafe_rows = [row for row in current if not row["safe"]]
        false_pass = sum(row["decision"] == "PASS" for row in unsafe_rows)
        safe_pass = sum(row["decision"] == "PASS" for row in safe_rows)
        unsafe_fail = sum(row["decision"] == "FAIL" for row in unsafe_rows)
        per_seed = []
        for seed in SEEDS:
            sr = [row for row in current if row["seed"] == seed]
            su = [row for row in sr if row["safe"]]
            uu = [row for row in sr if not row["safe"]]
            per_seed.append({"seed": seed, "unsafe_false_pass": sum(row["decision"] == "PASS" for row in uu) / len(uu), "safe_coverage": sum(row["decision"] == "PASS" for row in su) / len(su), "median_cost": median(float(row["cost"]) for row in sr)})
        result[policy] = {
            "n": len(current),
            "unsafe_false_pass_rate": false_pass / len(unsafe_rows),
            "unsafe_false_pass_ci": wilson(false_pass, len(unsafe_rows)),
            "safe_pass_coverage": safe_pass / len(safe_rows),
            "safe_pass_ci": wilson(safe_pass, len(safe_rows)),
            "unsafe_fail_coverage": unsafe_fail / len(unsafe_rows),
            "median_cost_to_decision": median(float(row["cost"]) for row in current),
            "budget_exceeded": sum(not bool(row["budget_ok"]) for row in current),
            "policy_trace_complete": all(isinstance(row["trace"], list) and len(row["trace"]) == int(row["steps"]) for row in current),
            "per_seed": per_seed,
            "safe_coverage_ci_across_seeds": mean_ci([item["safe_coverage"] for item in per_seed]),
            "median_cost_ci_across_seeds": mean_ci([item["median_cost"] for item in per_seed]),
        }
    return result


def main() -> int:
    out = Path(__file__).resolve().parent
    policies = ("uniform_eprocess", "random_eprocess", "risk_score_eprocess", "greedy_cost", "risk_score_naive", "rsap")
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        for episode in range(EPISODES_PER_SEED):
            for safe in (True, False):
                rng = random.Random(seed * 1000003 + episode * 97 + int(safe))
                uniforms = [rng.random() for _ in range(200)]
                for policy in policies:
                    rows.append({"seed": seed, **run_episode(policy, uniforms, safe, episode, budget=BUDGET)})
    write_jsonl(out / "raw_episodes_v2.jsonl", rows)
    summary = summarize(rows, policies)

    sensitivity: list[dict[str, object]] = []
    for budget in (40.0, 80.0, 120.0):
        for shift in (-0.02, 0.0, 0.02):
            test_rows = []
            for seed in SEEDS:
                for episode in range(200):
                    for safe in (True, False):
                        rng = random.Random(seed * 1000003 + episode * 97 + int(safe) + int(budget) * 11 + int((shift + 0.02) * 1000))
                        uniforms = [rng.random() for _ in range(200)]
                        test_rows.append({"seed": seed, **run_episode("rsap", uniforms, safe, episode, budget=budget, loss_shift=shift)})
            unsafe = [row for row in test_rows if not row["safe"]]
            safe_rows = [row for row in test_rows if row["safe"]]
            fp = sum(row["decision"] == "PASS" for row in unsafe)
            sensitivity.append({"budget": budget, "loss_shift": shift, "unsafe_false_pass_rate": fp / len(unsafe), "unsafe_false_pass_ci": wilson(fp, len(unsafe)), "safe_pass_coverage": sum(row["decision"] == "PASS" for row in safe_rows) / len(safe_rows), "budget_exceeded": sum(not row["budget_ok"] for row in test_rows)})

    proof = proof_audit()
    rsap = summary["rsap"]
    uniform = summary["uniform_eprocess"]
    paired_cost = [rsap["per_seed"][i]["median_cost"] - uniform["per_seed"][i]["median_cost"] for i in range(len(SEEDS))]
    paired_safe = [rsap["per_seed"][i]["safe_coverage"] - uniform["per_seed"][i]["safe_coverage"] for i in range(len(SEEDS))]
    stats = {"rsap_minus_uniform_median_cost_across_seed_ci": mean_ci(paired_cost), "rsap_minus_uniform_safe_coverage_across_seed_ci": mean_ci(paired_safe)}
    robustness_pass = all(item["unsafe_false_pass_ci"][1] <= ALPHA and item["budget_exceeded"] == 0 for item in sensitivity)
    status = "PASS" if rsap["unsafe_false_pass_ci"][1] <= ALPHA and rsap["safe_pass_coverage"] >= uniform["safe_pass_coverage"] and rsap["budget_exceeded"] == 0 and rsap["policy_trace_complete"] and proof["pass"] and robustness_pass else "FAIL"
    payload = {"candidate": "RSAP", "version": "v2-independent-proof-robustness", "status": status, "claim_state": "BOUNDED_SIMULATION_PASS" if status == "PASS" else "BOUNDED_SIMULATION_FAIL", "environment": environment_record(), "seeds": SEEDS, "episodes_per_seed": EPISODES_PER_SEED, "budget": BUDGET, "alpha": ALPHA, "actions": ACTIONS, "methods": summary, "paired_statistics": stats, "sensitivity": sensitivity, "proof_audit": proof, "docker": "NOT_TESTED", "enterprise_validity": "OUT_OF_SCOPE_BY_CONTRACT", "novelty": "NOT_PROVEN", "next_gate": "formal adaptive-filtration proof and external scheduler reproduction; enterprise deployment is out of scope"}
    write_json(out / "results_v2.json", payload)
    write_json(out / "results.json", payload)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
