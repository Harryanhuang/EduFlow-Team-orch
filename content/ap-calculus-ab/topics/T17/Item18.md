---
id: T17-Item18
difficulty: C
calculator: calc
type: frq
---
A particle moves along the $x$-axis with position $s(t) = t^4 - 8t^3 + 18t^2$ for $t \geq 0$, where $s$ is in meters and $t$ is in seconds.

**(a)** Find $v(t) = s'(t)$ and $a(t) = s''(t)$.

**(b)** Determine all times when the particle is at rest.

**(c)** Determine all times when the particle is speeding up versus slowing down.

**(d)** Determine all times when the particle changes direction.

**(e)** Find the total distance traveled by the particle from $t = 0$ to $t = 4$ seconds.

## Answer
**(a)**
$v(t) = s'(t) = 4t^3 - 24t^2 + 36t = 4t(t^2 - 6t + 9) = 4t(t - 3)^2$

$a(t) = s''(t) = 12t^2 - 48t + 36 = 12(t^2 - 4t + 3) = 12(t - 1)(t - 3)$

**(b)**
Particle at rest when $v(t) = 0$: $4t(t - 3)^2 = 0$

So $t = 0$ and $t = 3$ seconds.

**(c)**
Speeding up: $|v|$ increasing, which occurs when $v$ and $a$ have the same sign.

Sign analysis of $v$:
- $v(t) > 0$ for $t > 0$ (except $t = 3$ where $v = 0$)
- $v(0) = 0$

Sign analysis of $a$:
- $a(t) = 12(t - 1)(t - 3)$
- $a(t) > 0$ for $t < 1$ or $t > 3$
- $a(t) < 0$ for $1 < t < 3$

Speeding up:
- $0 < t < 1$: $v > 0$, $a > 0$ → speeding up
- $1 < t < 3$: $v > 0$, $a < 0$ → slowing down
- $t > 3$: $v > 0$, $a > 0$ → speeding up

Slowing down: $1 < t < 3$ (and possibly approaching $t = 0$ from the right, and $t = 3$ where $v = 0$)

**(d)**
Particle changes direction when $v$ changes sign: at $t = 0$ (starts from rest and moves positive), and... actually $v(t) = 4t(t-3)^2 \geq 0$ for all $t \geq 0$, so the particle never changes direction (always moving in positive direction after $t = 0$).

Wait, at $t = 0$, $v(0) = 0$, and then $v(t) > 0$ for $t > 0$, so direction doesn't change sign. The particle moves in the positive direction throughout.

**(e)**
To find total distance, integrate $|v(t)|$ from $t = 0$ to $t = 4$.

Since $v(t) \geq 0$ for all $t \geq 0$:
Distance $= \int_0^4 v(t) \, dt = s(4) - s(0) = (4^4 - 8 \cdot 4^3 + 18 \cdot 4^2) - 0 = (256 - 512 + 288) = 32$ meters.

## Explanation
This problem combines position/velocity/acceleration analysis with concavity (acceleration) to determine speeding up/slowing down, a common AP Calculus application.
