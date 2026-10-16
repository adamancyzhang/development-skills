#!/usr/bin/env python3
"""Deterministic grader for the comment-and-note-conventions behavior experiment.

Reads each run's revised file and compares it against ground_truth.json, then
writes grading.json (skill-creator schema) into the canonical run directory
(<eval>/<arm>/run-N/grading.json). No LLM involved.

Rules:
- KEEP item: PASS if any survival_key is found in the revised file text
  (case-insensitive; keys verified collision-free against scenario code tokens),
  or the original comment line is present verbatim. FAIL = over-deletion.
- DELETE / REWRITE item: PASS if the original comment line is no longer present
  verbatim (cleared or transformed). FAIL = wrong retention.
- Code-integrity smoke test: count of non-comment, non-blank lines must match
  the original (does not prove identity, only catches gross code changes).
"""
import json
from pathlib import Path

WS = Path(__file__).resolve().parent
IT = WS / "iteration-1"


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def original_line(text, marker):
    ml = marker.lower()
    for line in text.splitlines():
        if ml in line.lower():
            return line.strip()
    raise SystemExit(f"marker not found in scenario: {marker}")


def code_line_count(text):
    n = 0
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("//"):
            continue
        n += 1
    return n


def find_revised(out_dir, fname):
    d = Path(out_dir)
    exact = d / fname
    if exact.exists():
        return exact
    ext = Path(fname).suffix
    cands = sorted(p for p in d.glob(f"*{ext}") if p.is_file())
    return cands[0] if cands else None


def grade_run(scenario_name, comments, out_dir):
    src = (WS / "scenarios" / scenario_name).read_text(encoding="utf-8")
    revised_file = find_revised(out_dir, scenario_name)
    if revised_file is None:
        exps = [
            {"text": f"{c['id']} 承重/清理断言（{c['truth']}）", "passed": False,
             "evidence": f"输出文件缺失：{out_dir} 中找不到 {scenario_name}"}
            for c in comments
        ]
        return exps, [{"id": c["id"], "truth": c["truth"], "passed": False} for c in comments], None

    text = revised_file.read_text(encoding="utf-8")
    low = text.lower()
    lines = {l.strip() for l in text.splitlines()}
    exps, detail = [], []

    for c in comments:
        orig = original_line(src, c["marker"])
        verbatim = orig in lines
        if c["truth"] == "KEEP":
            survived = verbatim or any(k.lower() in low for k in c.get("survival_keys", []))
            passed = survived
            if verbatim:
                ev = f"原注释逐字保留：{orig[:90]}"
            elif survived:
                ev = "承重内容以改写形式存活（survival_key 命中）"
            else:
                ev = "误删：原注释与全部 survival_keys 均未出现在整理后的文件中"
            exp_text = f"{c['id']}·承重注释存活（{c['truth']}）— 删除即误删"
        else:
            passed = not verbatim
            ev = ("原注释行已不再逐字存在（已清除/转形）" if passed
                  else f"错误保留：原注释行仍逐字存在：{orig[:90]}")
            kind = "清理" if c["truth"] == "DELETE" else "转形"
            exp_text = f"{c['id']}·{kind}项已处理（{c['truth']}）— 原样保留即未达标"
        exps.append({"text": exp_text, "passed": passed, "evidence": ev})
        detail.append({"id": c["id"], "truth": c["truth"], "passed": passed})

    # code-integrity smoke test
    n0, n1 = code_line_count(src), code_line_count(text)
    exps.append({
        "text": "代码完整性冒烟：非注释行数量一致",
        "passed": n0 == n1,
        "evidence": f"原始 {n0} 行 vs 整理后 {n1} 行（仅冒烟，不证明逐行未改）",
    })
    return exps, detail, text


def main():
    gt = load_json(WS / "ground_truth.json")
    graded = 0
    for eval_dir in sorted(IT.glob("eval-*")):
        meta = load_json(eval_dir / "eval_metadata.json")
        scenario_name = meta["scenario"].split("/")[-1]
        comments = gt["scenarios"][scenario_name]["comments"]
        for arm_dir in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            for run_dir in sorted(arm_dir.glob("run-*")):
                run_dir = Path(run_dir)
                out = run_dir / "outputs"
                exps, detail, _ = grade_run(scenario_name, comments, out)
                passed = sum(1 for e in exps if e["passed"])
                total = len(exps)
                timing = {}
                tf = run_dir / "timing.json"
                if tf.exists():
                    timing = {"total_duration_seconds": load_json(tf).get("total_duration_seconds", 0.0)}
                out_chars = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) if out.exists() else 0
                grading = {
                    "expectations": exps,
                    "summary": {
                        "passed": passed, "failed": total - passed, "total": total,
                        "pass_rate": round(passed / total, 4) if total else 0.0,
                    },
                    "execution_metrics": {
                        "total_tool_calls": 0, "total_steps": 0, "errors_encountered": 0,
                        "output_chars": out_chars,
                        "files_created": [p.name for p in out.glob("*")] if out.exists() else [],
                    },
                    "timing": timing,
                    "detail": detail,
                }
                (run_dir / "grading.json").write_text(
                    json.dumps(grading, ensure_ascii=False, indent=2), encoding="utf-8")
                graded += 1
                print(f"graded {eval_dir.name}/{arm_dir.name}/{run_dir.name}: {passed}/{total}")
    print(f"done: {graded} runs graded")


if __name__ == "__main__":
    main()
