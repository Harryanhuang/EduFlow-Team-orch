---
id: T21-Item10
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int x\ln(x)\,dx\)

## Options
A) \(\frac{x^2}{2}\ln(x) - \frac{x^2}{4} + C\)
B) \(\frac{x^2}{2}\ln(x) + \frac{x^2}{4} + C\)
C) \(\frac{\ln(x)}{2} - \frac{1}{4x^2} + C\)
D) \(x\ln(x) - x + C\)

## Answer
A

## Explanation
Use integration by parts. Let:
- \(u = \ln(x)\) so \(du = \frac{1}{x}\,dx\)
- \(dv = x\,dx\) so \(v = \frac{x^2}{2}\)

\[
\int x\ln(x)\,dx = \frac{x^2}{2}\ln(x) - \int \frac{x^2}{2}\cdot\frac{1}{x}\,dx = \frac{x^2}{2}\ln(x) - \frac{1}{2}\int x\,dx
\]

\[
= \frac{x^2}{2}\ln(x) - \frac{1}{2}\cdot\frac{x^2}{2} + C = \frac{x^2}{2}\ln(x) - \frac{x^2}{4} + C
\]
