---
id: T02-Item14
difficulty: C
calculator: no-calc
type: frq
---
Let $g(x) = x \cos\left(\dfrac{1}{x^2}\right)$ for $x \neq 0$.

(a) Use the Squeeze Theorem to evaluate $\displaystyle \lim_{x \to 0} g(x)$.

(b) Explain why direct substitution fails for this limit.

## Answer
(a) 0

(b) Direct substitution gives $0 \cdot \cos(\text{undefined})$ because $\cos(1/x^2)$ oscillates without bound as $x \to 0$. The function $\cos(1/x^2)$ is not defined at $x = 0$, so direct substitution is not applicable.

## Explanation
**(a)** Since $-1 \leq \cos\left(\dfrac{1}{x^2}\right) \leq 1$ for all $x \neq 0$:

Multiplying by $x$, we must consider sign. For both $x > 0$ and $x < 0$:
$$-|x| \leq x \cos\left(\frac{1}{x^2}\right) \leq |x|$$

Since $\lim_{x \to 0} (-|x|) = 0$ and $\lim_{x \to 0} |x| = 0$, by the Squeeze Theorem:
$$\lim_{x \to 0} x \cos\left(\frac{1}{x^2}\right) = 0$$
