---
id: T20-Item07
difficulty: S
calculator: no-calc
type: mcq
---
If $G(x) = \int_2^{x^3} \sqrt{t^2 + 1} \, dt$, then $G'(x) =$

A) $\sqrt{x^6 + 1}$
B) $3x^2\sqrt{x^6 + 1}$
C) $\sqrt{(x^3)^2 + 1} - \sqrt{4 + 1}$
D) $x^2\sqrt{x^6 + 1}$

## Answer
B

## Explanation
This requires the Chain Rule combined with FTC Part 1.

Let $u = x^3$. Then $G(x) = \int_2^u f(t) \, dt$ where $f(t) = \sqrt{t^2 + 1}$.

By FTC Part 1: $\frac{d}{du}\left[\int_2^u f(t) \, dt\right] = f(u) = \sqrt{u^2 + 1}$

By the Chain Rule:
$$G'(x) = f(u) \cdot \frac{du}{dx} = \sqrt{(x^3)^2 + 1} \cdot 3x^2 = 3x^2\sqrt{x^6 + 1}$$
