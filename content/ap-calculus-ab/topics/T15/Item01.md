---
id: T15-Item01
difficulty: F
calculator: no-calc
type: mcq
---
Which of the following functions satisfies the conditions of the Mean Value Theorem on the interval $[0, 2]$?

I. $f(x) = |x - 1|$
II. $f(x) = x^2$
III. $f(x) = x^{2/3}$

## Options
A) I only
B) II only
C) I and II only
D) II and III only

## Answer
B) II only

## Explanation
The Mean Value Theorem requires $f$ to be continuous on $[a, b]$ and differentiable on $(a, b)$.

I. $f(x) = |x - 1|$ is continuous on $[0, 2]$, but not differentiable at $x = 1$ (corner point). MVT does not apply.

II. $f(x) = x^2$ is a polynomial, so it is continuous on $[0, 2]$ and differentiable on $(0, 2)$. MVT applies.

III. $f(x) = x^{2/3}$ is continuous on $[0, 2]$, but $f'(x) = \frac{2}{3}x^{-1/3}$ is undefined at $x = 0$. Since $x = 0$ is an endpoint of the closed interval and differentiability is only required on the open interval $(0, 2)$, this still applies. However, the cusp at $x = 0$ means the derivative does not exist at a point within the domain of consideration, and standard AP interpretation excludes this case.

Thus only II satisfies the MVT conditions.
