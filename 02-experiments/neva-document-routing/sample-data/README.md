# Test pile

Every page here is made from text we wrote or that is public domain, so the
correct text is known for every page. That known text is the answer key for CER.

| file | page type | how to make it | road expected |
|---|---|---|---|
| `born_digital.pdf` + `born_digital.txt` | PDF with a real text layer | write the text, export to PDF | A (docling) |
| `scanned_typed.pdf` + `scanned_typed.txt` | typed page, no text layer | print or render the text as an image, save the image as a PDF | B (OCR) |
| `handwritten.png` + `handwritten.txt` | handwritten page | write the known text by hand, photograph or scan it | B (OCR) |
| `old_book.png` + `old_book.txt` | old-book style page | public-domain page, or known text in a small serif font, downsampled and noised | B (OCR) |
| `image_only.png` + `image_only.txt` | an image file, not a PDF | any of the above saved as PNG | B (OCR) |

For each page, the `.txt` file holds the exact known text.

## Rules

- No real student work, no patient data, nothing under copyright.
- Keep each file small (one page, under 2 MB).
- For the resolution study, generate the lower-dpi copies inside the notebook
  from these originals; don't commit them.
