---
id: T09-Item08
difficulty: S
calculator: calc
type: mcq
---
Let h(x) = (3x + 1)⁵. What is the value of h''(1)?

## Options
A) 120
B) 1,080
C) 3,240
D) 5,760

## Answer
D) 5,760

## Explanation
First, find h'(x) using the chain rule:

h'(x) = 5(3x + 1)⁴ · d/dx[3x + 1] = 5(3x + 1)⁴ · 3 = **15(3x + 1)⁴**

Now find h''(x) by differentiating h'(x), again using the chain rule:

h''(x) = 15 · 4(3x + 1)³ · d/dx[3x + 1]
       = 15 · 4(3x + 1)³ · 3
       = **180(3x + 1)³**

Evaluate at x = 1:

h''(1) = 180(3(1) + 1)³ = 180 · 4³ = 180 · 64 = **5,760**

**Why the distractors are wrong:**
- A) 120 = 5! would come from mistakenly using just the factorial of the outer exponent, or computing 5 · 4 · (4)² = 120 · 4 = 480 / 4 = 120, which is not the correct formula.
- B) 1,080 = 5 · 4 · (3x+1)² · 3 · 3 evaluated incorrectly as 180 · 6 = 1,080 (forgetting to cube, using linear instead).
- C) 3,240 = 180 · 6² = 180 · 18, which would arise from computing (3x+1) as 6 instead of 4, or other arithmetic errors.
