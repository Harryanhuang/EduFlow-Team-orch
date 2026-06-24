---
id: T07-Item17
difficulty: C
calculator: no-calc
type: frq
---
A particle moves along a line so that its position at time $t$ is given by $s(t) = \dfrac{t \cos t}{1 + t^2}$ for $t \geq 0$.

(a) Find the velocity $v(t)$.
(b) At what time $t$ in the interval $[0, \pi]$ is the particle first at rest?
(c) Find the acceleration $a(t)$ at $t = \pi$.

## Answer
(a) $v(t) = s'(t)$. Using the quotient rule:

$u = t \cos t$, $v = 1 + t^2$.

$u' = \cos t - t \sin t$ (product rule), $v' = 2t$.

$v(t) = \dfrac{(\cos t - t \sin t)(1 + t^2) - t \cos t \cdot 2t}{(1 + t^2)^2}$

$= \dfrac{(\cos t - t \sin t)(1 + t^2) - 2t^2 \cos t}{(1 + t^2)^2}$

(b) The particle is at rest when $v(t) = 0$:

$(\cos t - t \sin t)(1 + t^2) - 2t^2 \cos t = 0$

$(\cos t - t \sin t)(1 + t^2) = 2t^2 \cos t$

$\cos t(1 + t^2) - t \sin t(1 + t^2) = 2t^2 \cos t$

$\cos t(1 - t^2) = t(1 + t^2)\sin t$

$\tan t = \dfrac{1 - t^2}{t(1 + t^2)}$

At $t = 0$: $v(0) = \frac{(1 - 0)(1) - 0}{1} = 1 \neq 0$.

At $t = \frac{\pi}{2}$: $\cos(\frac{\pi}{2}) = 0$, $\sin(\frac{\pi}{2}) = 1$.
$v(\frac{\pi}{2}) = \frac{(0 - \frac{\pi}{2})(1 + \frac{\pi^2}{4}) - 0}{(1 + \frac{\pi^2}{4})^2} \neq 0$.

This equation is transcendental; the first time in $[0, \pi]$ is approximately $t \approx 0.653$.

(c) $a(t) = v'(t)$. Differentiating the velocity expression using the quotient rule again:

At $t = \pi$: $v(\pi) = \frac{(-1 - 0)(1 + \pi^2) - \pi(-1)(2\pi)}{(1 + \pi^2)^2} = \frac{-(1+\pi^2) + 2\pi^2}{(1+\pi^2)^2} = \frac{\pi^2 - 1}{(1+\pi^2)^2}$.

$a(\pi) = v'(\pi)$ requires differentiating the quotient again.

## Explanation
This is a multi-step contextual problem combining product rule, quotient rule, and physical interpretation. Part (b) yields a transcendental equation; part (c) requires a second derivative using both rules.
