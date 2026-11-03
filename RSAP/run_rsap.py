from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from statistics import median

BUNDLE_ROOT = Path(__file__).resolve().parents[1]
ROOT = BUNDLE_ROOT if (BUNDLE_ROOT / "src").exists() else Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(BUNDLE_ROOT))

from assurance_lab import AnytimeCertificate, AnytimeStatus  # noqa: E402
from common import environment_record, wilson, write_json, write_jsonl  # noqa: E402


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
    if policy in {"greedy_cost", "peek_stop"}:
        return min(ACTIONS, key=lambda item: (item["cost"], item["id"]))
    if policy == "risk_score_naive":
        return max(ACTIONS, key=lambda item: ((TAU_UNSAFE - item["safe_loss"]) / item["cost"], -item["cost"]))
    if policy == "rsap":
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


def run_episode(policy: str, rng: random.Random, safe: bool, episode: int) -> dict[str, object]:
    certificate = None
    if policy in {"uniform_eprocess", "rsap"}:
        certificate = AnytimeCertificate(
            claim_id=f"rsap-{policy}-{episode}",
            claim_version="2026-11-03-v1",
            tau_unsafe=TAU_UNSAFE,
            tau_safe=TAU_SAFE,
            alpha_pass=ALPHA,
            alpha_fail=ALPHA,
            lambda_pass=0.5,
            lambda_fail=0.5,
        )
    counts = {action["id"]: 0 for action in ACTIONS}
    losses = {action["id"]: 0 for action in ACTIONS}
    trace: list[dict[str, object]] = []
    cost = 0.0
    decision = "UNKNOWN"
    for step in range(200):
        action = choose_action(policy, step, counts, losses)
        if cost + float(action["cost"]) > BUDGET:
            break
        probability = float(action["safe_loss"] if safe else action["unsafe_loss"])
        loss = int(rng.random() < probability)
        counts[str(action["id"])] += 1
        losses[str(action["id"])] += loss
        cost += float(action["cost"])
        if certificate is not None:
            update = certificate.update_loss(loss, evidence_id=f"{policy}-{episode}-{step}")
            decision = update.status.value
            trace.append({"step": step, "action": action["id"], "loss": loss, "cost": cost, "status": decision, "pass_wealth": update.pass_wealth, "fail_wealth": update.fail_wealth})
            if update.status in {AnytimeStatus.PASS, AnytimeStatus.FAIL, AnytimeStatus.CONFLICT, AnytimeStatus.INVALID}:
                break
        elif policy == "peek_stop":
            trace.append({"step": step, "action": action["id"], "loss": loss, "cost": cost, "status": "RUNNING"})
            if len(trace) >= 5:
                recent = [int(item["loss"]) for item in trace[-5:]]
                if sum(recent) <= 1:
                    decision = "PASS"
                    break
                if sum(recent) >= 4:
                    decision = "FAIL"
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
    return {"policy": policy, "safe": safe, "episode": episode, "decision": decision, "cost": cost, "steps": len(trace), "trace": trace, "budget_ok": cost <= BUDGET + 1e-12}


def main() -> int:
    out = Path(__file__).resolve().parent
    policies = ("uniform_eprocess", "greedy_cost", "risk_score_naive", "peek_stop", "rsap")
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for episode in range(EPISODES_PER_SEED):
            for safe in (True, False):
                for policy in policies:
                    result = run_episode(policy, rng, safe, episode)
                    rows.append({"seed": seed, **result})
    write_jsonl(out / "raw_episodes.jsonl", rows)
    summary: dict[str, object] = {}
    for policy in policies:
        policy_rows = [row for row in rows if row["policy"] == policy]
        safe_rows = [row for row in policy_rows if row["safe"]]
        unsafe_rows = [row for row in policy_rows if not row["safe"]]
        false_pass = sum(row["decision"] == "PASS" for row in unsafe_rows)
        safe_pass = sum(row["decision"] == "PASS" for row in safe_rows)
        fail = sum(row["decision"] == "FAIL" for row in unsafe_rows)
        costs = [float(row["cost"]) for row in policy_rows]
        summary[policy] = {
            "n": len(policy_rows),
            "unsafe_false_pass_rate": false_pass / len(unsafe_rows),
            "unsafe_false_pass_ci": wilson(false_pass, len(unsafe_rows)),
            "safe_pass_coverage": safe_pass / len(safe_rows),
            "safe_pass_ci": wilson(safe_pass, len(safe_rows)),
            "unsafe_fail_coverage": fail / len(unsafe_rows),
            "median_cost_to_decision": median(costs),
            "budget_exceeded": sum(not bool(row["budget_ok"]) for row in policy_rows),
            "policy_trace_complete": all(isinstance(row["trace"], list) and len(row["trace"]) == int(row["steps"]) for row in policy_rows),
        }
    rsap = summary["rsap"]
    rsap_upper = rsap["unsafe_false_pass_ci"][1]
    status = "PASS" if rsap_upper <= ALPHA and rsap["safe_pass_coverage"] >= summary["uniform_eprocess"]["safe_pass_coverage"] and rsap["budget_exceeded"] == 0 and rsap["policy_trace_complete"] else "FAIL"
    payload = {"candidate": "RSAP", "status": status, "claim_state": "BOUNDED_LOCAL_SELECTIVE_PASS" if status == "PASS" else "BOUNDED_LOCAL_SELECTIVE_FAIL", "environment": environment_record(), "seeds": SEEDS, "episodes_per_seed": EPISODES_PER_SEED, "budget": BUDGET, "alpha": ALPHA, "tau_safe": TAU_SAFE, "tau_unsafe": TAU_UNSAFE, "actions": ACTIONS, "methods": summary, "docker": "NOT_TESTED", "enterprise_validity": "NOT_TESTED", "novelty": "NOT_PROVEN", "next_gate": "Docker replay, proof audit under predictable adaptive filtration, and external baseline reproduction"}
    write_json(out / "results.json", payload)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
