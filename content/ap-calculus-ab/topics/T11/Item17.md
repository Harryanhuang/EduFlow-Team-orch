---
id: T11-Item17
difficulty: C
calculator: no-calc
type: frq
---
Let $g(x) = \arcsin x + \arccos x$ for $-1 \leq x \leq 1$.

(a) Find $g'(x)$.
(b) What does your answer to part (a) tell you about $g(x)$?
(c) Determine the constant value of $g(x)$ by evaluating at a convenient point.

## Answer
(a) $g'(x) = \frac{1}{\sqrt{1 - x^2}} + \frac{-1}{\sqrt{1 - x^2}} = 0$
(b) Since $g'(x) = 0$ for all $x$ in $(-1, 1)$, $g(x)$ is constant on its domain.
(c) $g(0) = \arcsin(0) + \arccos(0) = 0 + \frac{\pi}{2} = \frac{\pi}{2}$, so $g(x) = \frac{\pi}{2}$ for all $x \in [-1, 1]$.

## Explanation
Differentiating: $\frac{d}{dx}[\arcsin x] = \frac{1}{\sqrt{1-x^2}}$ and $\frac{d}{dx}[\arccos x] = \frac{-1}{\sqrt{1-x^2}}$. Their sum is identically zero, so $g$ is constant. Evaluating at $x = 0$ gives $g(0) = 0 + \frac{\pi}{2} = \frac{\pi}{2}$. This confirms the identity $\arcsin x + \arccos x = \frac{\pi}{2}$ for all $x \in [-1, 1]$.
