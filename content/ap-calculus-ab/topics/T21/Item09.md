---
id: T21-Item09
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int_1^e \frac{\ln(x)}{x}\,dx\)

## Options
A) 1
B) \(\frac{1}{2}\)
C) 2
D) \(\frac{e^2}{2} - \frac{1}{2}\)

## Answer
B

## Explanation
Use substitution. Let \(u = \ln(x)\), so \(du = \frac{1}{x}\,dx\).

When \(x = 1\), \(u = \ln(1) = 0\). When \(x = e\), \(u = \ln(e) = 1\).

\[
\int_1^e \frac{\ln(x)}{x}\,dx = \int_0^1 u\,du = \left[\frac{u^2}{2}\right]_0^1 = \frac{1}{2} - 0 = \frac{1}{2}
\]
