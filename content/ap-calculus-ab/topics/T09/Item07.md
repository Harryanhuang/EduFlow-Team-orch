---
id: T09-Item07
difficulty: S
calculator: no-calc
type: mcq
---
Let f(x) = |x² − 4|. Which of the following gives the value of f'(3)?

## Options
A) −6
B) 0
C) 6
D) The derivative does not exist at x = 3.

## Answer
C) 6

## Explanation
To differentiate f(x) = |x² − 4|, first express it piecewise.

|x² − 4| = x² − 4, when x² − 4 ≥ 0 (i.e., |x| ≥ 2)
|x² − 4| = −(x² − 4) = 4 − x², when x² − 4 < 0 (i.e., |x| < 2)

So f(x) can be written as:
- f(x) = x² − 4, for |x| ≥ 2
- f(x) = 4 − x², for |x| < 2

Differentiating each piece:
- For |x| > 2: f'(x) = 2x
- For |x| < 2: f'(x) = −2x
- At x = ±2: the derivative does not exist (the left and right derivatives disagree)

Since x = 3 satisfies |x| > 2, we use f'(x) = 2x:

**f'(3) = 2(3) = 6**

**Why the distractors are wrong:**
- A) −6 would be the answer if one used the wrong branch (the |x| < 2 branch) or forgot that x² − 4 > 0 at x = 3.
- B) 0 is the derivative at x = 0, not at x = 3.
- D) The derivative does not exist at x = ±2 (the "corners"), but x = 3 is a point where f is smooth.
