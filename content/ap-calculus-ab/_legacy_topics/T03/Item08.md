---
id: T03-Item08
difficulty: S
calculator: calc
type: frq
---

Let
\[
h(x) = \begin{cases}
\dfrac{\sin x}{x}, & x < 0 \\[6pt]
a, & x = 0 \\[6pt]
x^2 + b, & x > 0
\end{cases}
\]
Find the values of \( a \) and \( b \) for which \( h \) is continuous at \( x = 0 \).

## Answer
We need \( \displaystyle\lim_{x \to 0^-} h(x) = \displaystyle\lim_{x \to 0^+} h(x) = h(0) = a \).

Left-hand limit: \( \displaystyle\lim_{x \to 0^-} \frac{\sin x}{x} = 1 \) (standard limit).

Right-hand limit: \( \displaystyle\lim_{x \to 0^+} (x^2 + b) = b \).

Setting all three equal: \( 1 = a = b \).

Therefore \( a = 1 \) and \( b = 1 \).

## Explanation
Continuity at a point for a piecewise function requires matching the left-hand limit, right-hand limit, and function value. The well-known limit \( \displaystyle\lim_{x \to 0} \frac{\sin x}{x} = 1 \) provides the left-hand side. The polynomial piece provides the right-hand side directly. Both must equal the defined value at the point.
