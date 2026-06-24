---
id: T09-Item06
difficulty: S
calculator: calc
type: frq
---
A particle moves along a straight line. Its position at time $t$ (in seconds) is given by:

$$s(t) = \cos(t^2)$$

where $s$ is measured in centimeters.

(a) Find the velocity function $v(t)$.

(b) Find the acceleration function $a(t)$.

(c) Determine the velocity and acceleration of the particle at time $t = \sqrt{\pi}$. Include units.

## Answer
(a) $v(t) = -2t \sin(t^2)$

(b) $a(t) = -2\sin(t^2) - 4t^2 \cos(t^2)$

(c) $v(\sqrt{\pi}) = 0$ cm/s; $a(\sqrt{\pi}) = 4\pi$ cm/s$^2$

## Explanation

**(a) Velocity:** The velocity is the first derivative of position with respect to time.

$$v(t) = s'(t) = \frac{d}{dt}[\cos(t^2)]$$

Apply the chain rule with $u = t^2$:
- $\frac{d}{du}[\cos u] = -\sin u = -\sin(t^2)$
- $\frac{du}{dt} = 2t$

$$v(t) = -\sin(t^2) \cdot 2t = \mathbf{-2t \sin(t^2)}$$

**(b) Acceleration:** The acceleration is the derivative of velocity. Use the product rule on $v(t) = -2t \cdot \sin(t^2)$:

$$a(t) = v'(t) = \frac{d}{dt}[-2t \sin(t^2)]$$

Apply the product rule with $f = -2t$ and $g = \sin(t^2)$:
- $f' = -2$
- $g' = \cos(t^2) \cdot 2t = 2t \cos(t^2)$ (chain rule)

$$a(t) = f' \cdot g + f \cdot g' = (-2) \cdot \sin(t^2) + (-2t) \cdot (2t \cos(t^2))$$

$$a(t) = -2\sin(t^2) - 4t^2 \cos(t^2)$$

$$a(t) = \mathbf{-2\sin(t^2) - 4t^2 \cos(t^2)}$$

**(c) Evaluate at $t = \sqrt{\pi}$:**

For velocity, note that $(\sqrt{\pi})^2 = \pi$:

$$v(\sqrt{\pi}) = -2\sqrt{\pi} \cdot \sin(\pi) = -2\sqrt{\pi} \cdot 0 = \mathbf{0 \text{ cm/s}}$$

For acceleration:

$$a(\sqrt{\pi}) = -2\sin(\pi) - 4(\sqrt{\pi})^2 \cos(\pi)$$
$$= -2(0) - 4\pi \cdot (-1)$$
$$= 0 + 4\pi$$
$$= \mathbf{4\pi \text{ cm/s}^2}$$

At $t = \sqrt{\pi}$, the particle is momentarily at rest (velocity = 0) but accelerating at $4\pi$ cm/s$^2$ in the positive direction.
