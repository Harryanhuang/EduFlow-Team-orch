---
id: T03-Item15
difficulty: C
calculator: calc
type: frq
---

Let
\[
f(x) = \begin{cases}
\dfrac{x^2 - 4}{|x - 2|}, & x \neq 2 \\
k, & x = 2
\end{cases}
\]

(a) Evaluate \( \displaystyle\lim_{x \to 2^+} f(x) \) and \( \displaystyle\lim_{x \to 2^-} f(x) \).
(b) Does \( \displaystyle\lim_{x \to 2} f(x) \) exist? Justify your answer.
(c) Is there any value of \( k \) for which \( f \) is continuous at \( x = 2 \)? Explain.
(d) Classify the discontinuity at \( x = 2 \).

## Answer
(a) For \( x > 2 \): \( |x - 2| = x - 2 \), so
\[
f(x) = \frac{x^2 - 4}{x - 2} = \frac{(x+2)(x-2)}{x-2} = x + 2 \quad \text{for } x > 2.
\]
Thus \( \displaystyle\lim_{x \to 2^+} f(x) = 4 \).

For \( x < 2 \): \( |x - 2| = -(x - 2) = 2 - x \), so
\[
f(x) = \frac{x^2 - 4}{-(x - 2)} = -(x + 2) \quad \text{for } x < 2.
\]
Thus \( \displaystyle\lim_{x \to 2^-} f(x) = -4 \).

(b) No. Since the left-hand limit (\( -4 \)) and right-hand limit (\( 4 \)) are not equal, the two-sided limit does not exist.

(c) No value of \( k \) can make \( f \) continuous at \( x = 2 \). Continuity requires the limit to exist and equal \( f(2) \). Since the limit does not exist at \( x = 2 \), no assignment of \( k \) can achieve continuity.

(d) This is a **jump discontinuity** (non-removable), since both one-sided limits exist as finite values but disagree.

## Explanation
The absolute value in the denominator causes the expression to behave differently on each side of \( x = 2 \). After simplifying the rational expression piecewise, the mismatch in one-sided limits reveals a jump discontinuity that no redefinition can fix.
