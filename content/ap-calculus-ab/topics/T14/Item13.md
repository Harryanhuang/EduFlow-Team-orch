---
id: T14-Item13
difficulty: C
calculator: calc
type: frq
---
Let $f(x) = \cos x$ and let $L(x)$ be the linearization of $f$ at $x = 0$.

(a) Find $L(x)$.
(b) Use $L(x)$ to approximate $\cos(0.05)$.
(c) Determine whether the approximation in part (b) is an overestimate or underestimate. Justify your answer using the concavity of $f$.

## Answer
(a) $L(x) = 1$
(b) $\cos(0.05) \approx 1$
(c) Overestimate. Since $f''(x) = -\cos x < 0$ for $x$ near 0, the graph of $f$ is concave down at $x = 0$. A tangent line to a concave-down curve lies above the curve, so $L(0.05) > f(0.05)$, making the approximation an overestimate.

## Explanation
(a) $f(0) = \cos 0 = 1$, $f'(x) = -\sin x$, so $f'(0) = 0$. Thus $L(x) = 1 + 0(x - 0) = 1$.
(b) $L(0.05) = 1$.
(c) $f''(x) = -\cos x$. At $x = 0$, $f''(0) = -1 < 0$, so the graph is concave down near $x = 0$. The tangent line (linearization) lies above the curve, giving an overestimate.
