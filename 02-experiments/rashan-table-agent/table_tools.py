"""Table-aware tool: render a SciTableQA CSV as a clean markdown table.

This is the agent's 'table-aware' tool (vs a naive text dump). It fixes the two
Textract artifacts seen in SciTableQA Biology: a leading apostrophe on every cell
("'Exon 2 -> Exon 2) and trailing all-empty rows/cols. Keeping the header row and
column structure intact is the whole point — a naive splitter loses it.
"""
import csv
import io


def _clean(cell: str) -> str:
    c = (cell or "").strip()
    if c.startswith("'"):          # Textract prefixes text cells with a quote
        c = c[1:]
    return c.strip()


def csv_to_markdown(csv_text: str) -> str:
    rows = [[_clean(c) for c in r] for r in csv.reader(io.StringIO(csv_text))]
    rows = [r for r in rows if any(c for c in r)]          # drop empty rows
    # Textract appends a "Confidence Scores %" block below the real table — cut it.
    for i, r in enumerate(rows):
        if r and "confidence scores" in r[0].lower():
            rows = rows[:i]
            break
    if not rows:
        return "(empty table)"
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    # drop all-empty trailing columns
    while width > 1 and all(r[width - 1] == "" for r in rows):
        width -= 1
        rows = [r[:width] for r in rows]
    header, body = rows[0], rows[1:]
    out = ["| " + " | ".join(header) + " |",
           "| " + " | ".join(["---"] * width) + " |"]
    for r in body:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    from scitableqa_loader import load_biology
    t = load_biology(limit_qa_files=1)[0]
    print("naive text dump (first 3 lines):")
    print("\n".join(t.table_csv.splitlines()[:3]))
    print("\ntable-aware markdown:")
    print(csv_to_markdown(t.table_csv))


def csv_to_dataframe(csv_text: str):
    """Parse a SciTableQA CSV into a cleaned pandas DataFrame.

    Same cleaning as csv_to_markdown (strip Textract apostrophes, cut the
    appended 'Confidence Scores' block), but returns structured data so an agent
    can QUERY the table with code instead of re-typing values out of the prompt.
    Re-typing is where operand-selection errors come from.
    """
    import pandas as pd
    rows = [[_clean(c) for c in r] for r in csv.reader(io.StringIO(csv_text))]
    rows = [r for r in rows if any(c for c in r)]
    for i, r in enumerate(rows):
        if r and "confidence scores" in r[0].lower():
            rows = rows[:i]
            break
    if not rows:
        return pd.DataFrame()
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    header, body = rows[0], rows[1:]
    cols, seen = [], {}
    for j, h in enumerate(header):
        name = h.strip() or f"col{j}"
        seen[name] = seen.get(name, 0) + 1
        cols.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return pd.DataFrame(body, columns=cols)
