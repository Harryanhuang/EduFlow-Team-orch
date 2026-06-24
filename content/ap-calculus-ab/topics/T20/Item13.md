---
id: T20-Item13
difficulty: C
calculator: no-calc
type: mcq
---
Let $h(x) = \int_{x^2}^{3x} \cos(t) \, dt$. Which of the following gives $h'(x)$?

A) $\cos(3x) \cdot 3 - \cos(x^2) \cdot 2x$
B) $\cos(3x) - \cos(x^2)$
C) $\sin(3x) \cdot 3 - \sin(x^2) \cdot 2x$
D) $\cos(3x^2) \cdot 3 - \cos(x^4) \cdot 2x$

## Answer
A

## Explanation
This requires the Leibniz rule (generalized FTC with variable limits).

If $h(x) = \int_{u(x)}^{v(x)} f(t) \, dt$, then:
$$h'(x) = f(v(x)) \cdot v'(x) - f(u(x)) \cdot u'(x)$$

Here $f(t) = \cos(t)$, $v(x) = 3x$ (so $v'(x) = 3$), and $u(x) = x^2$ (so $u'(x) = 2x$).

$$h'(x) = \cos(3x) \cdot 3 - \cos(x^2) \cdot 2x = 3\cos(3x) - 2x\cos(x^2)$$

Option B forgets the chain rule factors. Option C incorrectly integrates instead of evaluating. Option D incorrectly substitutes the limits into the integrand.
