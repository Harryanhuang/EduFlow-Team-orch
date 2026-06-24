---
id: T20-Item09
difficulty: S
calculator: no-calc
type: frq
---
Let $F(x) = \int_0^x f(t) \, dt$ for $x \geq 0$, where $f$ is continuous and $f(2) = 5$.

(a) Find $F'(x)$ in terms of $f$.

(b) Find the derivative of $G(x) = F(3x + 1)$ with respect to $x$.

(c) If $H(x) = \int_2^x f(t) \, dt$, express $H(x)$ in terms of $F$.

## Answer
(a) $F'(x) = f(x)$

(b) $G'(x) = 3f(3x + 1)$

(c) $H(x) = F(x) - F(2) = F(x) - \int_0^2 f(t) \, dt$

## Explanation
(a) By FTC Part 1, $\frac{d}{dx}\int_0^x f(t) \, dt = f(x)$, so $F'(x) = f(x)$.

(b) Using the Chain Rule with FTC Part 1:
$G'(x) = F'(3x + 1) \cdot \frac{d}{dx}(3x + 1) = f(3x + 1) \cdot 3 = 3f(3x + 1)$

(c) Using the additivity property of definite integrals:
$$H(x) = \int_2^x f(t) \, dt = \int_0^x f(t) \, dt - \int_0^2 f(t) \, dt = F(x) - F(2)$$

This result holds regardless of whether $x > 2$ or $x < 2$ (with appropriate sign conventions for the integral).
