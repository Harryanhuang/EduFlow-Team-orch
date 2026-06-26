---
id: T05-Item12
difficulty: S
calculator: no-calc
type: frq
---
Consider the function
$$f(x) = \begin{cases} x^2 & \text{if } x \leq 1 \\ 2x - 1 & \text{if } x > 1 \end{cases}$$

(a) Is $f$ continuous at $x = 1$? Justify your answer.

(b) Is $f$ differentiable at $x = 1$? Justify your answer using the limit definition of the derivative.

## Answer
(a) Yes. $\lim_{x \to 1^-} f(x) = \lim_{x \to 1^-} x^2 = 1$ and $\lim_{x \to 1^+} f(x) = \lim_{x \to 1^+} (2x - 1) = 1$. Since both one-sided limits equal $f(1) = 1$, $f$ is continuous at $x = 1$.

(b) Check the one-sided limits of the difference quotient at $x = 1$:

Left-hand: $\displaystyle\lim_{h \to 0^-} \frac{f(1 + h) - f(1)}{h} = \lim_{h \to 0^-} \frac{(1+h)^2 - 1}{h} = \lim_{h \to 0^-} \frac{1 + 2h + h^2 - 1}{h} = \lim_{h \to 0^-} (2 + h) = 2$

Right-hand: $\displaystyle\lim_{h \to 0^+} \frac{f(1 + h) - f(1)}{h} = \lim_{h \to 0^+} \frac{[2(1+h) - 1] - 1}{h} = \lim_{h \to 0^+} \frac{2h}{h} = 2$

Since both one-sided limits equal 2, $f'(1) = 2$. Therefore $f$ is differentiable at $x = 1$.

## Explanation
This is an example where a piecewise function is both continuous AND differentiable at the boundary point. The key is that the pieces "meet" at $x = 1$ (continuity) and their slopes also match there (differentiability). Students should verify both conditions separately.
