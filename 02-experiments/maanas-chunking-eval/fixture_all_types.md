# Ghana Primary Mathematics Curriculum — Upper Primary (B4–B6)

This document is a benchmark fixture for chunking strategy evaluation. It
contains seven distinct data types, each clearly marked, so automated checks
can verify whether a chunker kept or broke each one.

## Rationale and Philosophy

The Ghana primary mathematics curriculum emphasises the development of
critical thinking and problem-solving abilities from the earliest years of
formal education. Learners are expected to build conceptual understanding
before procedural fluency, ensuring that mathematical ideas are not merely
memorised but deeply internalised. The curriculum draws on constructivist
pedagogy, where students actively construct knowledge through exploration,
discussion, and reflection rather than passive reception of facts.

Teachers are encouraged to use concrete manipulatives — such as base-ten
blocks, fraction strips, and number lines — before transitioning to pictorial
and then abstract representations. This concrete-pictorial-abstract (CPA)
progression is a deliberate instructional design choice grounded in decades of
mathematics education research. Assessment is formative and continuous:
teachers observe, question, and adapt their instruction based on what learners
demonstrate they understand, not solely on end-of-term examinations.

The integration of information and communication technology (ICT) is woven
throughout the curriculum as a cross-cutting competency. Learners use
calculators and simple spreadsheet tools to verify arithmetic, explore
patterns, and visualise data — not as a replacement for mental computation,
but as an additional lens through which mathematical relationships become
visible. This dual emphasis on manual skill and technological fluency
prepares students for both further academic study and real-world application.

## Strand 1: Number

### Sub-strand 1: Number and Numeration

#### B4.1.1.1 — Count, Read and Write Whole Numbers up to 100,000

Learners should be able to read and write whole numbers in both figures and
words up to one hundred thousand. The place-value system is extended from
the thousands (introduced in B3) to ten-thousands, reinforcing the pattern
that each position represents ten times the value of the position to its
right.

### Sub-strand 2: Number Operations

#### B4.1.2.1 — Addition and Subtraction of Four-Digit Numbers

Learners apply the standard algorithm for addition and subtraction with
regrouping (carrying and borrowing). Word problems should contextualise
operations in real-life situations — for example, market transactions,
distance calculations, and population comparisons — so that learners see
arithmetic as a tool for answering genuine questions, not an isolated drill.

## Content Standards and Indicators

The following table maps content standards to their indicators and exemplars
for the rounding and estimation strand. Each row is a self-contained
instructional target; splitting a row away from its column headers renders the
row's values meaningless.

| Content Standard | Indicator | Exemplar | Level | ICT Integration |
| --- | --- | --- | --- | --- |
| B4.1.1.1 Round whole numbers | B4.1.1.1.5 Round a number to the nearest ten, hundred or thousand | Round 14,765 to the nearest hundred → 14,800; Round 14,765 to the nearest thousand → 15,000 | B4 | Use a spreadsheet ROUND function to verify |
| B4.1.1.2 Compare and order | B4.1.1.2.1 Use inequality symbols to compare numbers up to 100,000 | 45,230 > 44,890; 12,005 < 12,050 | B4 | Display numbers on a number line applet |
| B5.1.2.1 Multiply multi-digit numbers | B5.1.2.1.3 Multiply a 3-digit number by a 2-digit number using the standard algorithm | 234 × 56 = 13,104 (partial products: 234×6=1,404; 234×50=11,700) | B5 | Calculator check; discuss when estimation suffices |
| B5.1.3.1 Fractions and decimals | B5.1.3.1.2 Convert between fractions and decimals | 3/4 = 0.75; 1/8 = 0.125; 2/5 = 0.4 | B5 | Fraction-to-decimal converter tool |
| B6.1.2.1 Order of operations | B6.1.2.1.1 Apply BODMAS to evaluate expressions | 8 + 4 × 3 = 20 (not 36); (8 + 4) × 3 = 36 | B6 | Evaluate with and without parentheses on a calculator |
| B6.1.4.1 Ratio and proportion | B6.1.4.1.2 Solve simple proportion problems | If 5 kg costs GHS 30, how much do 8 kg cost? → GHS 48 | B6 | Spreadsheet proportional fill |
| B6.1.5.1 Percentages | B6.1.5.1.1 Express fractions and decimals as percentages | 3/4 = 75%; 0.6 = 60%; 7/20 = 35% | B6 | Pie-chart generator with percentage labels |
| B4.1.2.2 Estimation strategies | B4.1.2.2.1 Estimate sums and differences before computing exact answers | Estimate 4,892 + 3,217 ≈ 5,000 + 3,000 = 8,000; exact = 8,109 | B4 | Mental math warm-up timer |

## Sample Grading Algorithm

The following Python function scores a student's arithmetic answer. It
demonstrates code with indentation, a docstring, a loop, conditional logic,
and a return value — all structures that a chunker might split incorrectly.

```python
def grade_arithmetic(student_answer: str, correct_answer: float,
                     tolerance: float = 0.01) -> dict:
    """Grade a single arithmetic response.

    Parameters
    ----------
    student_answer : str
        The student's raw text answer (may include units or whitespace).
    correct_answer : float
        The numerically correct value.
    tolerance : float
        Acceptable relative error (default 1%).

    Returns
    -------
    dict
        {"score": 0 or 1, "feedback": str}
    """
    # Strip non-numeric characters except decimal point and minus sign
    cleaned = ""
    for ch in student_answer.strip():
        if ch.isdigit() or ch in ".+-":
            cleaned += ch

    if not cleaned:
        return {"score": 0, "feedback": "No numeric value found in answer."}

    try:
        value = float(cleaned)
    except ValueError:
        return {"score": 0, "feedback": f"Could not parse '{cleaned}' as a number."}

    # Check relative error
    if correct_answer == 0:
        is_correct = abs(value) < tolerance
    else:
        relative_error = abs(value - correct_answer) / abs(correct_answer)
        is_correct = relative_error <= tolerance

    if is_correct:
        return {"score": 1, "feedback": "Correct."}
    else:
        return {
            "score": 0,
            "feedback": f"Expected {correct_answer}, got {value}."
        }
```

## Mathematical Expressions and Worked Examples

Below are sample mathematical expressions and worked solutions that appear
in student submissions and curriculum exemplars. A chunker must keep these
expressions intact — splitting between an opening `$` and its closing `$`, or
between a fraction's numerator and denominator, destroys the meaning.

**Arithmetic with regrouping:**

$230 + 160 = 390$

$4892 + 3217 = 8109$

$10000 - 6543 = 3457$

**Fractions and conversions:**

$\frac{3}{4} = 0.75 = 75\%$

$\frac{7}{20} = 0.35 = 35\%$

$\frac{1}{8} = 0.125 = 12.5\%$

**Order of operations (BODMAS):**

$8 + 4 \times 3 = 8 + 12 = 20$ (multiplication before addition)

$(8 + 4) \times 3 = 12 \times 3 = 36$ (parentheses override precedence)

**Algebraic identity:**

$x^2 + 2xy + y^2 = (x + y)^2$

**Ratio and proportion:**

If 5 kg of rice costs GHS 30, then 8 kg costs:

$\frac{8}{5} \times 30 = 48$ GHS

## Student Exam Submission — Transcribed

The following is a transcribed student exam answer (originally handwritten,
OCR-processed to HTML, then converted to text). It contains a question prompt
followed by the student's multi-step working and a teacher's annotation.

**Question 3 (5 marks):**
A farmer has 2,450 oranges. She packs them into crates of 35 oranges each.
(a) How many full crates does she fill?
(b) How many oranges are left over?
(c) If each full crate sells for GHS 12, how much money does she earn from
    selling all the full crates?

**Student Answer:**

Step 1: Divide total oranges by crate size.
$2450 \div 35 = 70$ remainder $0$

Step 2: Number of full crates = 70. Oranges left over = 0.

Step 3: Revenue from selling crates.
$70 \times 12 = 840$

Answer: (a) 70 full crates, (b) 0 left over, (c) GHS 840.

**Teacher Annotation:**
All three parts correct. Full marks (5/5). Student showed clear working
with correct use of long division and multiplication. Note: the student
initially wrote "$2450 \div 35 = 700$" but crossed it out and corrected to 70
— the self-correction demonstrates metacognitive monitoring.

## Bar Chart Description and Coordinate Grid

The following is a transcribed description of a bar chart and a coordinate
grid that appeared in a student's statistics assignment. Visual elements like
charts and grids are often reduced to text descriptions or ASCII art after
OCR; a chunker must keep the description together with its caption.

**Figure 1: Favourite Fruits Survey (B5 Class, 40 Students)**

```
Fruit       | Frequency | Bar (each * = 2 students)
------------|-----------|---------------------------
Mango       |    12     | * * * * * *
Orange      |     8     | * * * *
Banana      |     6     | * * *
Pineapple   |    10     | * * * * *
Pawpaw      |     4     | * *
```

Caption: The bar chart shows that mango is the most popular fruit (12
students), followed by pineapple (10), orange (8), banana (6), and pawpaw
(4). The modal fruit is mango. The range of frequencies is 12 − 4 = 8.

**Figure 2: Coordinate Grid — Plotting Points**

```
y
5 |           · (4,5)
4 |     · (2,4)
3 |               · (5,3)
2 |  · (1,2)
1 |        · (3,1)
0 +--+--+--+--+--+--→ x
  0  1  2  3  4  5
```

Caption: Five points are plotted on the first quadrant of a Cartesian plane:
(1,2), (2,4), (3,1), (4,5), and (5,3). Connecting them in order produces a
line graph with no clear linear trend — the relationship is non-linear.
Students should identify that (2,4) and (4,5) are above the line y = x, while
(3,1) and (5,3) are below it.

