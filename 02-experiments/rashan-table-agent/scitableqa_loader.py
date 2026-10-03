"""SciTableQA loader with a LOCAL cache — forms (question, gold GT, table) triples.

Provenance: SciTableQA, HuggingFace `Kehindeajayi01/SciTableQA` (MIT license).
Verified schema 2026-10-02: annotation JSONs under
  Annotated/ChatGPT/<Domain>/<layout>/<reasoning_type>/table-N_<paperid>.json
are LISTS of {QuestionID, Question, Answer (reference), QuestionType, TableName,
Explanation, GT}. Tables live at
  Amazon-Extracted-Tables/<Domain>/<layout>/<paperid>/<TableName>  (CSV).

Why a cache: the HF auto-viewer does not load (CSV column drift) and the dataset is
~893 MB, so we download only the domains we evaluate, ONCE, into data/scitableqa/.
Evaluation runs then make zero network calls. Paper-id separators differ between the
QA path ('_') and the table dir ('-'), so tables are joined on a normalized key.
Fail loud if the cache is missing rather than silently re-downloading mid-experiment.
"""
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass

API = "https://huggingface.co/api/datasets/Kehindeajayi01/SciTableQA?full=true"
BASE = "https://huggingface.co/datasets/Kehindeajayi01/SciTableQA/resolve/main/"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "scitableqa")
FILELIST = os.path.join(CACHE, "_filelist.json")


@dataclass
class Triple:
    question: str
    gold: str              # human ground truth (GT)
    reference_answer: str  # the dataset's own model answer, a baseline to compare
    reasoning_type: str
    table_csv: str
    table_path: str
    domain: str
    task_family: str = "Compute"
    grounded: bool = True   # gold text/number actually appears in the table


def norm_type(t: str) -> str:
    """Canonicalize reasoning-type labels: the dataset mixes case/spacing variants
    ('Cell Selection' vs 'Cell selection'), which would split the paper's tables."""
    t = re.sub(r"\s+", " ", (t or "").strip()).lower()
    alias = {"count": "counting", "total count": "counting",
             "percentage calculation": "percentage calculation",
             "max value identification": "identification",
             "direct information retrieval": "cell selection",
             "arithmetic involving cell selection": "arithmetic"}
    t = alias.get(t, t)
    return t.title() if t else "Unknown"


LOOKUP_TYPES = {"cell selection", "identification", "direct reading", "fact finding",
                "information retrieval", "lookup", "simple reading", "maximum value",
                "pattern identification", "simple"}


def is_grounded(gold: str, table_csv: str) -> bool:
    """True if the gold answer's text/number actually appears in the table.

    LABEL AUDIT: for a lookup question the gold must be a cell in the table. On
    SciTableQA Biology only ~80% of lookup golds are, because the annotations were
    made against the source papers while the tables here are Textract extractions.
    Ungrounded items cap achievable accuracy, so the paper reports the verifiable
    subset as the headline and the full set alongside it.
    """
    g = re.sub(r"[^a-z0-9.]", "", str(gold).lower())
    return bool(g) and g in re.sub(r"[^a-z0-9.]", "", str(table_csv).lower())


def task_family(reasoning_type: str) -> str:
    """Coarse split the paper reports on: find-a-cell vs compute-over-cells."""
    return "Lookup" if (reasoning_type or "").lower() in LOOKUP_TYPES else "Compute"


def _norm(s: str) -> str:
    """'12887_2014_Article_1190' == '12887-2014-Article-1190'."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _fetch(path: str) -> bytes:
    return urllib.request.urlopen(BASE + urllib.parse.quote(path), timeout=60).read()


def file_list(refresh: bool = False) -> list[str]:
    """Repo file list, cached locally (one API call ever)."""
    if not refresh and os.path.exists(FILELIST):
        return json.load(open(FILELIST))
    d = json.load(urllib.request.urlopen(API, timeout=60))
    files = [s["rfilename"] for s in d.get("siblings", [])]
    os.makedirs(CACHE, exist_ok=True)
    json.dump(files, open(FILELIST, "w"))
    return files


def _local(path: str) -> str:
    return os.path.join(CACHE, path)


def _save(path: str, blob: bytes) -> None:
    dest = _local(path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(blob)


def download_domain(domain: str = "Biology", limit_qa_files: int | None = None,
                    verbose: bool = True) -> dict:
    """Download one domain's annotation JSONs and their tables into the cache."""
    files = file_list()
    qa_files = sorted(p for p in files
                      if p.startswith(f"Annotated/ChatGPT/{domain}/") and p.endswith(".json"))
    if limit_qa_files:
        qa_files = qa_files[:limit_qa_files]
    table_idx = {}
    for p in files:
        if p.startswith(f"Amazon-Extracted-Tables/{domain}/") and p.endswith(".csv"):
            parts = p.split("/")
            if "Other" in parts:          # skip alternate-extraction copies
                continue
            table_idx[(_norm(parts[-2]), parts[-1].lower())] = p

    got_qa = got_tbl = skipped = 0
    for i, qp in enumerate(qa_files, 1):
        if not os.path.exists(_local(qp)):
            try:
                _save(qp, _fetch(qp))
            except Exception:
                continue
            got_qa += 1
        try:
            items = json.loads(open(_local(qp), "rb").read())
        except Exception:
            continue
        m = re.match(r"table-\d+_(.+)$", os.path.basename(qp)[:-5])
        if not m:
            continue
        paperid = _norm(m.group(1))
        for it in items:
            tp = table_idx.get((paperid, str(it.get("TableName", "")).lower()))
            if not tp:
                skipped += 1
                continue
            if not os.path.exists(_local(tp)):
                try:
                    _save(tp, _fetch(tp))
                    got_tbl += 1
                except Exception:
                    pass
        if verbose and i % 25 == 0:
            print(f"  {domain}: {i}/{len(qa_files)} qa files "
                  f"(+{got_qa} qa, +{got_tbl} tables)", flush=True)
    stats = {"domain": domain, "qa_files": len(qa_files), "downloaded_qa": got_qa,
             "downloaded_tables": got_tbl, "qa_items_without_table": skipped}
    if verbose:
        print(f"  {domain} done: {stats}", flush=True)
    return stats


def load_domain(domain: str = "Biology", limit_qa_files: int | None = None) -> list[Triple]:
    """Read triples from the LOCAL cache. Raises if the domain was not downloaded."""
    root = os.path.join(CACHE, "Annotated", "ChatGPT", domain)
    if not os.path.isdir(root):
        raise RuntimeError(
            f"SciTableQA '{domain}' is not in the local cache ({root}). "
            f"Run:  python scitableqa_loader.py --download {domain}")
    qa_files = []
    for dirpath, _, names in os.walk(root):
        qa_files += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    qa_files.sort()
    if limit_qa_files:
        qa_files = qa_files[:limit_qa_files]

    # index cached tables for this domain
    tbl_root = os.path.join(CACHE, "Amazon-Extracted-Tables", domain)
    idx = {}
    for dirpath, _, names in os.walk(tbl_root):
        for n in names:
            if n.endswith(".csv") and os.path.basename(dirpath) != "Other":
                idx[(_norm(os.path.basename(dirpath)), n.lower())] = os.path.join(dirpath, n)

    triples, missing = [], 0
    for qp in qa_files:
        m = re.match(r"table-\d+_(.+)$", os.path.basename(qp)[:-5])
        if not m:
            continue
        paperid = _norm(m.group(1))
        try:
            items = json.loads(open(qp, "rb").read())
        except Exception:
            continue
        for it in items:
            tp = idx.get((paperid, str(it.get("TableName", "")).lower()))
            if not tp:
                missing += 1
                continue
            triples.append(Triple(
                question=it.get("Question", ""),
                gold=str(it.get("GT", "")),
                reference_answer=str(it.get("Answer", "")),
                reasoning_type=norm_type(str(it.get("QuestionType", ""))),
                table_csv=open(tp, encoding="utf-8", errors="replace").read(),
                table_path=os.path.relpath(tp, CACHE),
                domain=domain,
                task_family=task_family(norm_type(str(it.get("QuestionType", "")))),
                grounded=is_grounded(str(it.get("GT", "")),
                                     open(tp, encoding="utf-8", errors="replace").read())))
    if missing:
        print(f"[warn] {missing} QA items had no cached table (skipped)")
    return triples


# backward-compatible helper used by earlier scripts
def load_biology(limit_qa_files: int | None = None) -> list[Triple]:
    return load_domain("Biology", limit_qa_files)


if __name__ == "__main__":
    import argparse
    from collections import Counter
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", metavar="DOMAIN", help="e.g. Biology, CompSci, MatSci")
    ap.add_argument("--limit-qa-files", type=int, default=None)
    ap.add_argument("--stats", metavar="DOMAIN", help="summarize the local cache")
    a = ap.parse_args()
    if a.download:
        download_domain(a.download, a.limit_qa_files)
    if a.stats:
        t = load_domain(a.stats)
        print(f"{a.stats}: {len(t)} triples")
        print("by reasoning type:", dict(Counter(x.reasoning_type for x in t)))
