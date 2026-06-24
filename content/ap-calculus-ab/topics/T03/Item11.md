---
id: T03-Item11
difficulty: C
calculator: no-calc
type: frq
---

Determine whether the function
\[
f(x) = \begin{cases}
\dfrac{|x - 1|}{x - 1}, & x \neq 1 \\
0, & x = 1
\end{cases}
\]
is continuous at \( x = 1 \). If not, classify the discontinuity and explain why it cannot be removed by redefining \( f(1) \).

## Answer
For \( x > 1 \): \( \dfrac{|x - 1|}{x - 1} = \dfrac{x - 1}{x - 1} = 1 \). So \( \displaystyle\lim_{x \to 1^+} f(x) = 1 \).

For \( x < 1 \): \( \dfrac{|x - 1|}{x - 1} = \dfrac{-(x - 1)}{x - 1} = -1 \). So \( \displaystyle\lim_{x \to 1^-} f(x) = -1 \).

Since the left-hand limit (\( -1 \)) and right-hand limit (\( 1 \)) exist but are not equal, \( \displaystyle\lim_{x \to 1} f(x) \) does not exist. Therefore \( f \) is discontinuous at \( x = 1 \).

This is a **jump discontinuity**. It cannot be removed because the left-hand and right-hand limits disagree; no single value assigned to \( f(1) \) can make the limit equal to the function value.

## Explanation
The absolute value function creates different expressions on either side of the critical point. When the one-sided limits exist but disagree, the discontinuity is a jump, which is inherently non-removable since no redefinition at the point can bridge the gap.
