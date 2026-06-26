---
id: T09-Item10
difficulty: S
calculator: calc
type: mcq
---
Let f(x) = √(cos(eˣ)). What is the value of f'(0)?

## Options
A) −sin(1) / (2√(cos(1)))
B) −e · sin(1) / (2√(cos(1)))
C) −sin(1) / √(cos(1))
D) sin(1) / (2√(cos(1)))

## Answer
A) −sin(1) / (2√(cos(1)))

## Explanation
The function f(x) = √(cos(eˣ)) = [cos(eˣ)]^(1/2) is a composition of three functions. Apply the chain rule working from the outside in:

**Layer 1 (outer):** d/du[u^(1/2)] = (1/2)u^(−1/2) = 1/(2√u), where u = cos(eˣ)

**Layer 2 (middle):** d/dv[cos v] = −sin v, where v = eˣ

**Layer 3 (inner):** d/dx[eˣ] = eˣ

Combining all three layers:

f'(x) = (1/2) · [cos(eˣ)]^(−1/2) · [−sin(eˣ)] · eˣ

f'(x) = **−eˣ · sin(eˣ) / (2√(cos(eˣ)))**

Evaluate at x = 0:
- e⁰ = 1
- sin(e⁰) = sin(1)
- cos(e⁰) = cos(1)

**f'(0) = −1 · sin(1) / (2√(cos(1))) = −sin(1) / (2√(cos(1)))**

**Why the distractors are wrong:**
- B) Includes a spurious factor of e, as if one evaluated eˣ as e instead of e⁰ = 1.
- C) Is missing the factor of 1/2 from differentiating the square root (the power rule step).
- D) Has the wrong sign, as if the negative from differentiating cos was dropped.
