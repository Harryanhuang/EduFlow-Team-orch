---
id: T14-Item03
difficulty: S
calculator: no-calc
type: frq
---
Consider $f(x) = \sqrt{x}$.

(a) Find the linearization $L(x)$ of $f$ at $x = 4$.
(b) Use $L(x)$ to approximate $\sqrt{4.41}$.
(c) Without using a calculator, state whether the approximation in part (b) is an overestimate or underestimate. Justify your answer.

## Answer
(a) $L(x) = 2 + \frac{1}{4}(x-4)$
(b) $L(4.41) = 2 + \frac{1}{4}(0.41) = 2 + 0.1025 = 2.1025$
(c) Since $f''(x) = -\frac{1}{4x^{3/2}} < 0$ for all $x > 0$, $f$ is concave down at $x = 4$. A tangent line to a concave-down curve lies above the curve, so the linearization overestimates: $\sqrt{4.41} \approx 2.1025 > \sqrt{4.41} \approx 2.1$. The approximation is an overestimate.

## Explanation
(a) $f(4) = 2$, $f'(x) = \frac{1}{2\sqrt{x}}$, so $f'(4) = \frac{1}{4}$. Thus $L(x) = 2 + \frac{1}{4}(x-4)$.
(b) $L(4.41) = 2 + \frac{0.41}{4} = 2 + 0.1025 = 2.1025$.
(c) Second derivative test: $f''(x) = -\frac{1}{4x^{3/2}} < 0$, confirming concave down and hence an overestimate.
