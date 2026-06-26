---
id: T20-Item15
difficulty: C
calculator: calc
type: frq
---
Let $f$ be a differentiable function with $f(0) = 3$ and $f(5) = 8$. Define $A(x) = \int_0^x f(t) \, dt$ for all real $x$.

(a) Find $A(5)$ in terms of $f$.

(b) Find $A'(0)$.

(c) Show that there exists a number $c$ in $(0, 5)$ such that $A''(c) = 1$.

(d) Given that $f'(x) = \frac{x}{f(x)}$, find $A(x)$.

## Answer
(a) $A(5) = \int_0^5 f(t) \, dt$

(b) $A'(0) = f(0) = 3$

(c) By the Mean Value Theorem for Integrals: $\int_0^5 f(t) \, dt = f(c) \cdot 5$ for some $c \in (0, 5)$.
By FTC: $A(5) = \int_0^5 f(t) \, dt$.
Since $A(0) = 0$ and $A(5) = 5 \cdot f(c)$ for some $c$,
$A'(c) = \frac{A(5) - A(0)}{5 - 0} = \frac{5f(c)}{5} = f(c)$.
By MVT for derivatives on $[0, 5]$: $A'(5) - A'(0) = A''(c)(5 - 0)$ for some $c$.
$f(5) - f(0) = 5A''(c)$
$8 - 3 = 5A''(c)$
$5 = 5A''(c)$
$A''(c) = 1$ ✓

(d) From $f'(x) = \frac{x}{f(x)}$:
$f'(x) = \frac{1}{2}\frac{d}{dx}[f(x)^2]$ (by chain rule)
$2f'(x) = \frac{d}{dx}[f(x)^2]$
Integrating: $f(x)^2 = x^2 + C$
$f(0) = 3$: $9 = 0 + C$, so $C = 9$
$f(x)^2 = x^2 + 9$, and since $f(0) = 3 > 0$, $f(x) = \sqrt{x^2 + 9}$
$A(x) = \int_0^x \sqrt{t^2 + 9} \, dt = \frac{x}{2}\sqrt{x^2 + 9} + \frac{9}{2}\ln\left|\frac{x + \sqrt{x^2 + 9}}{3}\right|$
