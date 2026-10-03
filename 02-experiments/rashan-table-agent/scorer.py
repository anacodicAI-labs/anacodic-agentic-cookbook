"""Scorer: is a predicted answer correct against the gold GT?

SciTableQA answers are short strings like '48 nucleotides', '3', '11.3%'. We
score with normalized match: lowercase, strip units/punctuation, and compare the
numeric core when both sides contain a number (so '48 nucleotides' == '48'). This
is deliberately strict-but-fair; an LLM judge can be layered on later for the
free-text cases. Reported numbers always state which scorer produced them.
"""
import re


def _num(s: str):
    m = re.search(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s.replace(",", ""))
    return float(m.group()) if m else None


def _close(a: float, b: float, rel: float = 1e-2) -> bool:
    """Numeric match with RELATIVE tolerance.

    Gold answers are often rounded differently from a computed value
    ('0.00034' vs '3.42E-04', '14.47%' vs '14.5%'). An absolute 1e-6 test marks
    those wrong even though they agree to the precision the gold is stated at,
    so we allow a small relative difference.
    """
    if a == b:
        return True
    scale = max(abs(a), abs(b))
    return scale > 0 and abs(a - b) / scale <= rel


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9.]", "", (s or "").lower())


def is_correct(pred: str, gold: str, question: str = "") -> bool:
    """Normalized match. For 'difference' questions the sign is not meaningful
    (the dataset's gold is unsigned, e.g. gold '3' for a 20-vs-23 comparison),
    so magnitudes are compared there; elsewhere the sign must match."""
    if pred is None or gold is None:
        return False
    gp, gg = _num(pred), _num(gold)
    if gp is not None and gg is not None:
        if _close(gp, gg):
            return True
        if "difference" in (question or "").lower() and _close(abs(gp), abs(gg)):
            return True
        return False
    return _norm(pred) == _norm(gold) or _norm(gold) in _norm(pred)


if __name__ == "__main__":
    from collections import Counter
    from scitableqa_loader import load_biology
    trips = load_biology(limit_qa_files=8)
    by_type = Counter()
    correct_by_type = Counter()
    n_ok = 0
    for t in trips:
        ok = is_correct(t.chatgpt_answer, t.gold)
        n_ok += ok
        by_type[t.reasoning_type] += 1
        correct_by_type[t.reasoning_type] += ok
    print(f"\nChatGPT baseline (no table tool) on {len(trips)} Biology questions:")
    print(f"  accuracy = {n_ok}/{len(trips)} = {n_ok/len(trips):.1%}")
    print("  by reasoning type (correct/total):")
    for rt in sorted(by_type):
        print(f"    {rt:28s} {correct_by_type[rt]:2d}/{by_type[rt]:<2d}")
