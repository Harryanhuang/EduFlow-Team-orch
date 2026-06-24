---
id: T17-Item13
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = x \cdot e^{x^2}$.

**(a)** Find $f'(x)$ and $f''(x)$.

**(b)** Determine all points where $f$ has local extrema. Justify your answer using the Second Derivative Test.

**(c)** Determine all points of inflection of $f$. Justify your answer.

**(d)** On what intervals is $f$ concave up? Justify using $f''(x)$.

## Answer
**(a)** 
Using the product rule: $f'(x) = e^{x^2} + x \cdot e^{x^2} \cdot 2x = e^{x^2}(1 + 2x^2)$

Using the product rule again: $f''(x) = e^{x^2} \cdot 2x(1 + 2x^2) + e^{x^2} \cdot 4x = 2xe^{x^2}(1 + 2x^2) + 4xe^{x^2} = 2xe^{x^2}(1 + 2x^2 + 2) = 2xe^{x^2}(3 + 2x^2)$

**(b)** 
Critical points occur when $f'(x) = 0$: $e^{x^2}(1 + 2x^2) = 0$

Since $e^{x^2} > 0$ for all $x$ and $1 + 2x^2 \geq 1 > 0$, there are no critical points where $f'(x) = 0$.

Therefore, $f$ has no local extrema.

**(c)**
Set $f''(x) = 0$: $2xe^{x^2}(3 + 2x^2) = 0$

Since $e^{x^2} > 0$ and $3 + 2x^2 > 0$, we have $2x = 0$, so $x = 0$.

Test concavity on either side:
- For $x < 0$: $f''(x) < 0$ (concave down)
- For $x > 0$: $f''(x) > 0$ (concave up)

Since concavity changes at $x = 0$, the point of inflection is at $x = 0$.

**(d)**
Since $e^{x^2} > 0$ and $3 + 2x^2 > 0$ for all $x$, the sign of $f''$ depends on $x$:
- $f''(x) < 0$ when $x < 0$ (concave down)
- $f''(x) > 0$ when $x > 0$ (concave up)

Therefore, $f$ is concave up on $(0, \infty)$.

## Explanation
This problem requires finding and analyzing derivatives, applying the Second Derivative Test, identifying inflection points by checking sign changes, and determining concavity intervals from $f''$.
