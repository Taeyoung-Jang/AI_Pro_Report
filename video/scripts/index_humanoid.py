"""휴머노이드 3시드 실험의 실행별 결과·변경 축·영상 경로를 표로 정리한다.

사용: python -I index_humanoid.py <humanoid_reasoning_fallback3 디렉터리> <출력 json>
"""
import glob
import json
import os
import sys

root, out = sys.argv[1], sys.argv[2]
rows = []
for path in sorted(glob.glob(os.path.join(root, "seed_*/reports/*/*_attempts.json"))):
    seed, method = os.path.basename(path).split("_")[:2]
    attempts_dir = os.path.join(root, f"seed_{seed}/seeds/{seed}/{method}/attempts")
    for rec in json.load(open(path)):
        ep, cand = rec["episode"], rec["candidate"]
        ev = cand.get("evidence") or {}
        tax = ep.get("taxonomy") or {}
        res_path = os.path.join(attempts_dir, rec["id"], "rollout/result.json")
        res = json.load(open(res_path)) if os.path.exists(res_path) else {}
        rows.append({
            "seed": int(seed),
            "method": method,
            "attempt": rec["id"],
            "outcome": ep.get("task_outcome"),
            "termination": ep.get("termination_reason"),
            "taxonomy": tax,
            "changed_axes": cand.get("changed_axes") or [],
            "after": (cand.get("branch_audit") or {}).get("after"),
            "target_family": ev.get("target_family"),
            "hypothesis": ev.get("hypothesis"),
            "goal_distance_m": res.get("goal_distance_m"),
            "sim_s": ep.get("simulation_s"),
            "wall_s": rec["receipt"].get("wall_s"),
            "robot_api_calls": ep.get("robot_api_calls"),
            "video": os.path.join(attempts_dir, rec["id"], "rollout/rollout.mp4"),
        })
json.dump(rows, open(out, "w"), ensure_ascii=False, indent=1)
for r in rows:
    print(r["seed"], r["method"], r["attempt"], r["outcome"], r["termination"],
          r["changed_axes"], r["after"], r["target_family"],
          json.dumps(r["taxonomy"], ensure_ascii=False)[:120],
          r["goal_distance_m"] and round(r["goal_distance_m"], 2), r["sim_s"] and round(r["sim_s"]),
          r["wall_s"] and round(r["wall_s"]))
