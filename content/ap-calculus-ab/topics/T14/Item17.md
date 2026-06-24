---
id: T14-Item17
difficulty: C
calculator: calc
type: frq
---
A function $f$ satisfies $f(4) = 3$, $f'(4) = -1$, and $f''(x) > 0$ for all $x > 0$.

(a) Find the linearization $L(x)$ of $f$ at $x = 4$.
(b) Using $L(x)$, estimate $f(4.3)$.
(c) Explain why $f(4.3) < L(4.3)$ must be true.
(d) The actual value of $f(4.3)$ is 2.71. Find the approximation error $E = f(4.3) - L(4.3)$. What can you say about the sign of $E$ based on the concavity of $f$?

## Answer
(a) $L(x) = 3 - (x - 4) = 7 - x$
(b) $L(4.3) = 7 - 4.3 = 2.7$
(c) Since $f''(x) > 0$ for all $x > 0$, $f$ is concave up. A tangent line to a concave-up curve lies below the curve, so $f(4.3) > L(4.3)$.
(d) $E = 2.71 - 2.7 = 0.01$. Since $f$ is concave up ($f'' > 0$), the actual value exceeds the linear approximation, so $E > 0$. The error is positive.

## Explanation
(a) $L(x) = f(4) + f'(4)(x - 4) = 3 + (-1)(x - 4) = 7 - x$.
(b) $L(4.3) = 7 - 4.3 = 2.7$.
(c) Concavity test: if $f'' > 0$, the graph lies above its tangent line.
(d) The actual error is positive, consistent with concave-up behavior.
