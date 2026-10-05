"""Optional — add DISTRACTOR papers: same-topic articles with no questions.

    python download_distractors.py              # 1,500 papers (default)
    python download_distractors.py --n 200      # smaller

Why: with only the 147 question papers in the index, search is easy — the
answer is in 1 of 147. Real systems search tens of thousands of papers, many
on the same topic. Distractors hide each answer among ~1,600 papers so
Recall@k and context precision fall to an honest level. Questions still point
only at the original papers; retrieving a distractor counts as a miss.

Selection (reproducible): PMC search
    (COVID-19 OR SARS-CoV-2 OR coronavirus)[Title], open access, CC BY licence,
    published 2020-2021
→ first 10,000 hits → random sample with --seed (default 42), excluding every
COVID-QA article, then the same licence / retraction / PDF checks as
download.py (CC0 / CC BY family only, never retracted).

Output (gitignored): data/pdfs/PMC*.pdf (alongside the question papers) and
data/manifest_distractors.csv — one row per distractor with its licence.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import urllib.parse

from download import DATA, PMC_BUCKET, REDISTRIBUTABLE, fetch, pmc_metadata

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&retmode=json"
QUERY = ('(COVID-19[Title] OR SARS-CoV-2[Title] OR coronavirus[Title]) '
         'AND "open access"[filter] AND "cc by license"[filter] AND 2020:2021[pdat]')


def search_ids(limit: int = 10_000) -> list[str]:
    ids: list[str] = []
    for start in range(0, limit, 5_000):
        url = (f"{ESEARCH}&retmax=5000&retstart={start}&sort=relevance"
               f"&term={urllib.parse.quote(QUERY)}")
        page = json.loads(fetch(url))["esearchresult"]["idlist"]
        ids += [f"PMC{i}" for i in page]
        if len(page) < 5_000:
            break
    return ids


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    question_papers = {r["pmcid"] for r in csv.DictReader(open(DATA / "manifest.csv"))}
    pool = [i for i in search_ids() if i not in question_papers]
    random.Random(args.seed).shuffle(pool)
    print(f"pool {len(pool)} candidates · sampling until {args.n} usable PDFs")

    rows, kept = [], 0
    for pmcid in pool:
        if kept >= args.n:
            break
        meta = pmc_metadata(pmcid)
        row = {"pmcid": pmcid, "doi": "", "title": "", "license": "", "pdf": "", "status": ""}
        if not meta:
            row["status"] = "not in PMC Cloud"
        else:
            row.update(doi=meta.get("doi") or "", title=(meta.get("title") or "")[:150],
                       license=meta.get("license_code") or "")
            if meta.get("is_retracted"):
                row["status"] = "retracted — skipped"
            elif row["license"] not in REDISTRIBUTABLE:
                row["status"] = f"licence {row['license'] or 'unknown'} — skipped"
            elif not meta.get("pdf_url"):
                row["status"] = "no PDF — skipped"
            else:
                key = meta["pdf_url"].split("pmc-oa-opendata/")[1].split("?")[0]
                dest = DATA / "pdfs" / f"{pmcid}.pdf"
                if not dest.exists():
                    fetch(f"{PMC_BUCKET}/{key}", dest)
                row.update(pdf=f"pdfs/{dest.name}", status="pdf")
                kept += 1
                if kept % 100 == 0:
                    print(f"  {kept} distractor PDFs")
        rows.append(row)

    with open(DATA / "manifest_distractors.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{kept} distractor PDFs (checked {len(rows)}) → data/manifest_distractors.csv")


if __name__ == "__main__":
    main()
