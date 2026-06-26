---
id: T01-Item16
difficulty: C
calculator: no-calc
type: mcq
---
Let \(f(x) = x \cdot \sin\left(\dfrac{1}{x}\right)\) for \(x \neq 0\). Which statement about \(\displaystyle\lim_{x \to 0} f(x)\) is correct?

## Options
A) The limit does not exist because \(\sin(1/x)\) oscillates infinitely often near \(x = 0\).
B) The limit is 0 by the Squeeze Theorem, since \(-|x| \leq f(x) \leq |x|\).
C) The limit is 1 because \(\sin(1/x)\) approaches 1 as \(x \to 0\).
D) The limit does not exist because \(f(0)\) is undefined.

## Answer
B

## Explanation
For all \(x \neq 0\), we have \(-1 \leq \sin(1/x) \leq 1\), so \(-|x| \leq x \cdot \sin(1/x) \leq |x|\). Since \(\lim_{x \to 0}(-|x|) = 0\) and \(\lim_{x \to 0}|x| = 0\), by the Squeeze Theorem, \(\displaystyle\lim_{x \to 0} x \cdot \sin\left(\frac{1}{x}\right) = 0\). This is a classic example where oscillation does not prevent a limit from existing — the amplitude shrinks to 0.
