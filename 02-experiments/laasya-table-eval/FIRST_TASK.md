# Your first task

**Task:** audit 60 table questions by hand. **Time:** ~2-3 hours.
**You need:** no coding, no API key.

This is the most important open question in the project right now, and it is
work only a careful human can do.

## Start here

1. Do `SETUP_FIRST.md` once (fork, clone, branch) - 10 minutes, with Rashan.
2. Open **`audit/AUDIT_INSTRUCTIONS.md`** and follow it. It has the definitions,
   the rules, and a fully worked example from our real data.
3. Work through `audit/items.md`, filling in `audit/audit_sheet.csv`.
4. Write 5-8 sentences of findings in `results/NOTES.md`.
5. Commit and open a Pull Request.

## Why this is your contribution

We are measuring whether an AI agent can answer questions whose answers live in
tables. We already found a case where the benchmark's "correct" answer (48)
cannot be obtained from the table it gives us (which supports 46). If that is
common, every accuracy number in the study is partly measuring bad labels rather
than a bad model.

Nobody can settle that with code - it needs a person to read each table and
judge. Your audit decides how the whole paper reports its results, which is why
it is a first-author contribution.

## Optional, afterwards

`analyze_results.py` turns result CSVs into accuracy tables and a figure:

```bash
python 02-experiments/laasya-table-eval/analyze_results.py
```

It already runs on a real sample in `results-input/`. Later you will own the
accuracy-by-question-type tables and figures for the paper.

## The one rule

> Only edit files inside `laasya-table-eval/`. Never change anyone else's folder.

That is what lets several people work in the same repository without breaking
each other's work. Nothing you do here can damage the project, and nothing is
final until a Pull Request is reviewed.
