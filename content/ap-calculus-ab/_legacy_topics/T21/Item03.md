---
id: T21-Item03
difficulty: F
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int e^{5x}\,dx\)

## Options
A) \(5e^{5x} + C\)
B) \(\frac{1}{5}e^{5x} + C\)
C) \(e^{5x} + C\)
D) \(e^{5x} \cdot 5x + C\)

## Answer
B

## Explanation
Use substitution. Let \(u = 5x\), so \(du = 5\,dx\) and \(dx = \frac{du}{5}\).

\[
\int e^{5x}\,dx = \int e^u \cdot \frac{du}{5} = \frac{1}{5}\int e^u\,du = \frac{1}{5}e^u + C = \frac{1}{5}e^{5x} + C
\]

The antiderivative of \(e^{kx}\) is \(\frac{1}{k}e^{kx} + C\).
