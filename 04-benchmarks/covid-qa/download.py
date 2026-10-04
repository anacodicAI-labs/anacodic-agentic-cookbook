"""Step 1 of 3 — fetch COVID-QA and the original article PDFs.

    python download.py              # everything (~150 PDFs)
    python download.py --limit 5    # a quick pilot

What it does
  1. COVID-QA.json (deepset, Apache-2.0): 2,019 expert questions over 147
     full-text articles, each answer marked as a span in the article text.
  2. Finds each article's PMC ID (from the text header, else via NCBI's ID
     converter using the DOI).
  3. Reads the article's metadata from the PMC Cloud Service (public AWS
     bucket, no login): licence, retraction flag, PDF location.
  4. Downloads the PDF ONLY when the licence allows redistribution
     (CC0 / CC BY / CC BY-SA / CC BY-ND) and the article is not retracted.
  5. Writes data/manifest.csv — one row per article, with the licence and
     the reason when a PDF was not fetched.

Articles without a usable PDF keep their questions: step 2 falls back to the
article text COVID-QA itself ships, and marks those chunks source="dataset_text".

Output (all gitignored):  data/COVID-QA.json · data/pdfs/PMC*.pdf · data/manifest.csv
Source acknowledgement: NIH NLM NCBI PubMed Central (PMC) Article Datasets,
https://registry.opendata.aws/ncbi-pmc · COVID-QA, deepset (Apache-2.0).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
COVIDQA_URL = ("https://raw.githubusercontent.com/deepset-ai/COVID-QA/master/"
               "data/question-answering/COVID-QA.json")
PMC_BUCKET = "https://pmc-oa-opendata.s3.amazonaws.com"
IDCONV = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/?format=json&ids="
REDISTRIBUTABLE = {"CC0", "CC BY", "CC BY-SA", "CC BY-ND"}


def fetch(url: str, dest: Path | None = None, timeout: int = 120) -> bytes:
    """curl, not urllib: some cluster Pythons fail TLS handshakes curl handles."""
    cmd = ["curl", "-sSL", "--fail", "--max-time", str(timeout), url]
    if dest:
        cmd += ["-o", str(dest)]
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def header_fields(context: str) -> dict:
    head = context[:1500]
    pmc = re.search(r"PMC(\d+)", head)
    doi = re.search(r"DOI:\s*(\S+)", head)
    return {
        "title": head.split("\n")[0].strip(),
        "pmcid": f"PMC{pmc.group(1)}" if pmc else "",
        "doi": doi.group(1).replace("https://doi.org/", "") if doi else "",
    }


def resolve_dois(rows: list[dict]) -> None:
    todo = [r for r in rows if not r["pmcid"] and r["doi"]]
    if not todo:
        return
    ids = ",".join(r["doi"] for r in todo)
    recs = json.loads(fetch(IDCONV + urllib.parse.quote(ids, safe=",/"))).get("records", [])
    by_doi = {x.get("doi", "").lower(): x.get("pmcid", "") for x in recs}
    for r in todo:
        r["pmcid"] = by_doi.get(r["doi"].lower(), "") or ""


def pmc_metadata(pmcid: str) -> dict | None:
    """Metadata of the newest version that RECORDS a licence, else the newest.

    Some later versions carry license_code=null while version 1 says CC BY;
    a licence granted for a version still applies to that version, so we use
    the newest version whose licence is on record and fetch THAT version's PDF.
    """
    versions = []
    for v in range(1, 6):
        try:
            versions.append(json.loads(
                fetch(f"{PMC_BUCKET}/{pmcid}.{v}/{pmcid}.{v}.json", timeout=60)))
        except subprocess.CalledProcessError:
            break
    if not versions:
        return None
    licensed = [m for m in versions if m.get("license_code")]
    chosen = licensed[-1] if licensed else versions[-1]
    chosen["is_retracted"] = any(m.get("is_retracted") for m in versions)
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only the first N articles")
    args = ap.parse_args()

    (DATA / "pdfs").mkdir(parents=True, exist_ok=True)
    qa_path = DATA / "COVID-QA.json"
    if not qa_path.exists():
        fetch(COVIDQA_URL, qa_path)
    articles = json.loads(qa_path.read_text())["data"]

    rows = []
    for i, art in enumerate(articles[: args.limit]):
        para = art["paragraphs"][0]
        rows.append({"doc_index": i, **header_fields(para["context"]),
                     "n_questions": len(para["qas"])})
    resolve_dois(rows)

    for r in rows:
        r.update({"license": "", "is_retracted": "", "pdf": "", "status": ""})
        if not r["pmcid"]:
            r["status"] = "no PMC copy — use dataset text"
            continue
        meta = pmc_metadata(r["pmcid"])
        if not meta:
            r["status"] = "not in PMC Cloud — use dataset text"
            continue
        r["license"] = meta.get("license_code") or ""
        r["is_retracted"] = meta.get("is_retracted")
        r["doi"] = r["doi"] or (meta.get("doi") or "")
        if meta.get("is_retracted"):
            r["status"] = "retracted — skipped"
        elif r["license"] not in REDISTRIBUTABLE:
            r["status"] = f"licence {r['license'] or 'unknown'} — use dataset text"
        elif not meta.get("pdf_url"):
            r["status"] = "no PDF in PMC — use dataset text"
        else:
            key = meta["pdf_url"].split("pmc-oa-opendata/")[1].split("?")[0]
            dest = DATA / "pdfs" / f"{r['pmcid']}.pdf"
            if not dest.exists():
                fetch(f"{PMC_BUCKET}/{key}", dest)
            r["pdf"] = f"pdfs/{dest.name}"
            r["status"] = "pdf"
        print(f"{r['doc_index']:>3} {r['pmcid'] or '-':<12} {r['license'] or '-':<8} {r['status']}")

    with open(DATA / "manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_pdf = sum(r["status"] == "pdf" for r in rows)
    print(f"\n{n_pdf}/{len(rows)} articles with a redistributable PDF · "
          f"{sum(r['n_questions'] for r in rows)} questions · manifest: data/manifest.csv")


if __name__ == "__main__":
    main()
