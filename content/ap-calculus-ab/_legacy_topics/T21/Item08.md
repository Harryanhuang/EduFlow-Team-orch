---
id: T21-Item08
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int x^2 e^{x^3}\,dx\)

## Options
A) \(\frac{1}{3}e^{x^3} + C\)
B) \(e^{x^3} + C\)
C) \(3e^{x^3} + C\)
D) \(\frac{x^3}{3}e^{x^3} + C\)

## Answer
A

## Explanation
Use substitution. Let \(u = x^3\), so \(du = 3x^2\,dx\) and \(x^2\,dx = \frac{du}{3}\).

\[
\int x^2 e^{x^3}\,dx = \int e^u \cdot \frac{du}{3} = \frac{1}{3}\int e^u\,du = \frac{1}{3}e^u + C = \frac{1}{3}e^{x^3} + C
\]
