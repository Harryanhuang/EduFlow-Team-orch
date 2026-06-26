---
id: T21-Item06
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate: \(\displaystyle \int x\sqrt{x-3}\,dx\)

## Options
A) \(\frac{2}{5}(x-3)^{5/2} + \frac{6}{5}(x-3)^{3/2} + C\)
B) \(\frac{2}{5}x(x-3)^{5/2} + C\)
C) \(\frac{2}{3}(x-3)^{3/2} + C\)
D) \(\frac{2}{5}(x-3)^{5/2} + 2(x-3)^{3/2} + C\)

## Answer
D

## Explanation
Use substitution. Let \(u = x - 3\), so \(x = u + 3\) and \(dx = du\).

\[
\int x\sqrt{x-3}\,dx = \int (u+3)u^{1/2}\,du = \int (u^{3/2} + 3u^{1/2})\,du
\]

Integrate:

\[
\int u^{3/2}\,du = \frac{2}{5}u^{5/2},\quad \int 3u^{1/2}\,du = 3\cdot\frac{2}{3}u^{3/2} = 2u^{3/2}
\]

So: \(\frac{2}{5}(x-3)^{5/2} + 2(x-3)^{3/2} + C\)
