---
id: T01-Item17
difficulty: C
calculator: no-calc
type: frq
---
Let
\[
h(x) = \begin{cases}
\sin\left(\dfrac{1}{x}\right), & x \neq 0 \\
0, & x = 0
\end{cases}
\]

(a) Does \(\displaystyle\lim_{x \to 0} h(x)\) exist? Justify your answer carefully.
(b) Does \(\displaystyle\lim_{x \to 0} x^2 \cdot h(x)\) exist? If so, find it and justify.
(c) Compare parts (a) and (b). Explain why multiplying by \(x^2\) changes the answer.

## Answer
(a) The limit does not exist.
(b) The limit is 0.
(c) The factor \(x^2\) squeezes the oscillation amplitude to 0.

## Explanation
(a) As \(x \to 0\), the quantity \(1/x\) grows without bound, so \(\sin(1/x)\) oscillates between \(-1\) and \(1\) infinitely often. There is no single value \(L\) such that \(h(x)\) gets arbitrarily close to \(L\) as \(x \to 0\). For example, along the sequence \(x_n = \frac{1}{2\pi n}\), we get \(h(x_n) = 0\), but along \(x_n = \frac{1}{\pi/2 + 2\pi n}\), we get \(h(x_n) = 1\). Since different sequences approaching 0 give different limit values, the limit does not exist.
(b) We have \(-x^2 \leq x^2 \cdot \sin(1/x) \leq x^2\) for all \(x \neq 0\). Since both \(-x^2 \to 0\) and \(x^2 \to 0\) as \(x \to 0\), the Squeeze Theorem gives \(\displaystyle\lim_{x \to 0} x^2 \cdot h(x) = 0\).
(c) In part (a), the oscillation has fixed amplitude 1, so no single limiting value exists. In part (b), the factor \(x^2\) forces the amplitude to shrink to 0 as \(x \to 0\), so regardless of how fast \(\sin(1/x)\) oscillates, the values are squeezed into an envelope that collapses to 0.
