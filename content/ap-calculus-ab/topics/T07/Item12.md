---
id: T07-Item12
difficulty: S
calculator: no-calc
type: frq
---
Let $g(x) = \dfrac{\cos x}{1 + \sin x}$. Find $g'(x)$ and simplify your answer.

## Answer
$g'(x) = \dfrac{-1}{1 + \sin x}$

## Explanation
Using the quotient rule: $u = \cos x$, $v = 1 + \sin x$, $u' = -\sin x$, $v' = \cos x$.

$g'(x) = \frac{-\sin x(1 + \sin x) - \cos x \cdot \cos x}{(1 + \sin x)^2} = \frac{-\sin x - \sin^2 x - \cos^2 x}{(1 + \sin x)^2}$

Since $\sin^2 x + \cos^2 x = 1$: $g'(x) = \frac{-\sin x - 1}{(1 + \sin x)^2} = \frac{-(1 + \sin x)}{(1 + \sin x)^2} = \frac{-1}{1 + \sin x}$.
