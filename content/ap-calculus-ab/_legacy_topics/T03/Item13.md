---
id: T03-Item13
difficulty: S
calculator: no-calc
type: frq
---

Let \( f(x) = \dfrac{x^3 - 8}{x - 2} \).

(a) Show that \( f \) has a removable discontinuity at \( x = 2 \).
(b) Define a function \( g \) that extends \( f \) to be continuous at \( x = 2 \). State the value of \( g(2) \).

## Answer
(a) \( f \) is undefined at \( x = 2 \) (denominator is zero). Factoring:
\[
\frac{x^3 - 8}{x - 2} = \frac{(x - 2)(x^2 + 2x + 4)}{x - 2} = x^2 + 2x + 4 \quad \text{for } x \neq 2.
\]
Thus \( \displaystyle\lim_{x \to 2} f(x) = 4 + 4 + 4 = 12 \), which exists. Since the limit exists but \( f(2) \) is undefined, the discontinuity is removable.

(b) Define
\[
g(x) = \begin{cases}
\dfrac{x^3 - 8}{x - 2}, & x \neq 2 \\
12, & x = 2
\end{cases}
\]
Then \( g(2) = 12 \), and \( g \) is continuous at \( x = 2 \).

## Explanation
A removable discontinuity can be "filled in" by defining (or redefining) the function at the point to equal the limit. The key step is factoring to evaluate the limit.
