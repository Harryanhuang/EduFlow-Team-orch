---
id: T21-Item02
difficulty: F
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int \sin(3x)\,dx\)

## Options
A) \(-\cos(3x) + C\)
B) \(-\frac{1}{3}\cos(3x) + C\)
C) \(\frac{1}{3}\cos(3x) + C\)
D) \(3\cos(3x) + C\)

## Answer
B

## Explanation
Use substitution. Let \(u = 3x\), so \(du = 3\,dx\) and \(dx = \frac{du}{3}\).

\[
\int \sin(3x)\,dx = \int \sin(u)\cdot\frac{du}{3} = \frac{1}{3}\int \sin(u)\,du = -\frac{1}{3}\cos(u) + C = -\frac{1}{3}\cos(3x) + C
\]

Remember to divide by the inner derivative.
