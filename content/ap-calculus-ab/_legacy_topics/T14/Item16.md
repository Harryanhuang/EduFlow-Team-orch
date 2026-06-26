---
id: T14-Item16
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{x}{e^x - 1}$.

(a) Evaluate $\displaystyle \lim_{x \to 0} f(x)$ using L'Hôpital's Rule.
(b) Use the linearization of $f$ at $x = 0$ to confirm the result of part (a).
(c) Without using a calculator, determine whether $f(0.1)$ is greater than or less than $f(0)$. Justify your answer.

## Answer
(a) $\displaystyle \lim_{x \to 0} \frac{x}{e^x - 1} = 1$
(b) The linearization is $L(x) = 1 - \frac{x}{2}$. Evaluating at $x = 0$ gives $L(0) = 1$, confirming the limit from part (a).
(c) $f(0.1) > f(0)$. Since $f''(0) = \frac{1}{6} > 0$, $f$ is concave up near $x = 0$. A concave-up curve lies above its tangent line, so $f(0.1) > L(0.1) = 1 - \frac{0.1}{2} = 0.95$. Since $f(0) = 1$, we have $f(0.1) > 0.95$ while $f(0) = 1$ exactly. More directly: since $f$ is concave up and the tangent line lies below the curve for $x \neq 0$, we have $f(0.1) > L(0.1)$. Comparing $f(0.1)$ to $f(0)$: since $f'(0) = -\frac{1}{2} < 0$, $f$ is decreasing at $x = 0$, so $f(0.1) < f(0) = 1$.

## Explanation
(a) As $x \to 0$, numerator $\to 0$ and denominator $\to 0$. Apply L'Hôpital's Rule: $\lim_{x \to 0} \frac{1}{e^x} = 1$.
(b) From the power series $f(x) = 1 + \frac{x}{2} - \frac{x^2}{12} + \cdots$, we get $f(0) = 1$ and $f'(0) = -\frac{1}{2}$. Thus $L(x) = 1 - \frac{x}{2}$, and $L(0) = 1$, confirming the limit.
(c) Since $f'(0) = -\frac{1}{2} < 0$, $f$ is strictly decreasing through $x = 0$. Therefore $f(0.1) < f(0) = 1$. (Alternatively, since $f''(0) = -\frac{1}{6} < 0$, the function is concave down near $x = 0$, and a tangent line to a concave-down curve lies above the curve, so $f(0.1) < L(0.1) = 0.95 < 1 = f(0)$. Both approaches confirm $f(0.1) < f(0)$.)
