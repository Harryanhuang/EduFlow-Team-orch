---
id: T21-Item07
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int \cos^3(x)\sin^2(x)\,dx\)

## Options
A) \(\frac{\sin^3(x)}{3} - \frac{\sin^5(x)}{5} + C\)
B) \(\frac{\cos^4(x)}{4} - \frac{\cos^6(x)}{6} + C\)
C) \(\frac{\sin^3(x)}{3} + \frac{\sin^5(x)}{5} + C\)
D) \(\frac{\cos^4(x)}{4} + \frac{\cos^6(x)}{6} + C\)

## Answer
A

## Explanation
Use the "odd power" strategy. Since \(\cos^3(x) = \cos^2(x)\cos(x) = (1-\sin^2(x))\cos(x)\):

Let \(u = \sin(x)\), so \(du = \cos(x)\,dx\).

\[
\int \cos^3(x)\sin^2(x)\,dx = \int (1-u^2)u^2\,du = \int (u^2 - u^4)\,du
\]

\[
= \frac{u^3}{3} - \frac{u^5}{5} + C = \frac{\sin^3(x)}{3} - \frac{\sin^5(x)}{5} + C
\]
