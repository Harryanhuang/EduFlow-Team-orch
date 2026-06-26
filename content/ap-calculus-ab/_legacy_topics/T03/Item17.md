---
id: T03-Item17
difficulty: C
calculator: no-calc
type: frq
---

Let \( f(x) = \dfrac{\sin(\pi x)}{x^2 - x} \).

(a) Determine all points of discontinuity of \( f \).
(b) For each point found in (a), classify the discontinuity as removable or non-removable, with justification.
(c) Define a function \( F \) that agrees with \( f \) everywhere except at the removable discontinuities, where \( F \) is continuous. Give the values of \( F \) at those points.

## Answer
(a) The denominator factors as \( x^2 - x = x(x - 1) \). The function is undefined at \( x = 0 \) and \( x = 1 \). These are the discontinuities.

(b)
- At \( x = 0 \): Using \( \displaystyle\lim_{x \to 0} \frac{\sin(\pi x)}{x} = \pi \) and \( x^2 - x = x(x-1) \), we have
\[
\lim_{x \to 0} \frac{\sin(\pi x)}{x(x-1)} = \lim_{x \to 0} \frac{\sin(\pi x)}{x} \cdot \frac{1}{x-1} = \pi \cdot (-1) = -\pi.
\]
The limit exists, so \( x = 0 \) is a **removable discontinuity**.

- At \( x = 1 \): Let \( u = x - 1 \). As \( x \to 1 \), \( u \to 0 \):
\[
\lim_{x \to 1} \frac{\sin(\pi x)}{x(x-1)} = \lim_{u \to 0} \frac{\sin(\pi(u+1))}{(u+1)u} = \lim_{u \to 0} \frac{-\sin(\pi u)}{(u+1)u} = \lim_{u \to 0} \frac{-\sin(\pi u)}{u} \cdot \frac{1}{u+1} = -\pi \cdot 1 = -\pi.
\]
The limit exists, so \( x = 1 \) is also a **removable discontinuity**.

(c) Define
\[
F(x) = \begin{cases}
\dfrac{\sin(\pi x)}{x^2 - x}, & x \neq 0, 1 \\
-\pi, & x = 0 \\
-\pi, & x = 1
\end{cases}
\]
Then \( F \) is continuous at \( x = 0 \) and \( x = 1 \).

## Explanation
Both discontinuities are removable because the sine zeros cancel with the polynomial zeros in the denominator. The key technique is rewriting using the standard limit \( \sin(\pi u)/u \to \pi \).
