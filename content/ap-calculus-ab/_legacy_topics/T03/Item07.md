---
id: T03-Item07
difficulty: C
calculator: no-calc
type: frq
---

Let \( g(x) = \dfrac{x^2 - 5x + 6}{x^2 - 4} \).

(a) Find all values of \( x \) at which \( g \) is discontinuous.
(b) Classify each discontinuity as removable or non-removable (and if non-removable, specify whether it is a jump or infinite discontinuity).
(c) Define a function \( G \) that agrees with \( g \) everywhere except at the removable discontinuities, where \( G \) is continuous. Give the values of \( G \) at those points.

## Answer
(a) Factor both numerator and denominator:
- Numerator: \( x^2 - 5x + 6 = (x - 2)(x - 3) \)
- Denominator: \( x^2 - 4 = (x - 2)(x + 2) \)

\( g \) is undefined when the denominator is zero: \( x = 2 \) and \( x = -2 \).

(b)
- At \( x = 2 \): The factor \( (x - 2) \) cancels, so \( \displaystyle\lim_{x \to 2} g(x) = \displaystyle\lim_{x \to 2} \frac{x - 3}{x + 2} = \frac{-1}{4} \). The limit exists but \( g(2) \) is undefined, so **removable discontinuity**.
- At \( x = -2 \): After simplification, \( g(x) = \dfrac{x - 3}{x + 2} \). As \( x \to -2 \), the numerator approaches \( -5 \neq 0 \) and the denominator approaches 0, so \( g(x) \to \pm\infty \). Thus **infinite discontinuity** (vertical asymptote).

(c) Define
\[
G(x) = \begin{cases}
\dfrac{x^2 - 5x + 6}{x^2 - 4}, & x \neq 2 \\
-\dfrac{1}{4}, & x = 2
\end{cases}
\]
Then \( G(2) = -\dfrac{1}{4} \), and \( G \) is continuous at \( x = 2 \). (The discontinuity at \( x = -2 \) is non-removable, so no redefinition helps there.)

## Explanation
Rational functions are continuous wherever the denominator is nonzero. A common factor in numerator and denominator signals a removable discontinuity; a denominator-only zero after canceling common factors signals an infinite discontinuity. Extending the function at a removable discontinuity requires defining the value to equal the limit.
