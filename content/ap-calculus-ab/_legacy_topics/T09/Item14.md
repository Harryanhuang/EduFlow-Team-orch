---
id: T09-Item14
difficulty: C
calculator: calc
type: frq
---
A particle moves along a straight line with position given by $s(t) = \ln(\cos(t))$ for $0 < t < \dfrac{\pi}{2}$.

(a) Find the velocity $v(t)$ and acceleration $a(t)$ of the particle.

(b) Determine whether the particle is ever at rest on the interval $0 < t < \dfrac{\pi}{2}$. Justify your answer.

(c) Find the total distance traveled by the particle from $t = \dfrac{\pi}{6}$ to $t = \dfrac{\pi}{4}$.

## Answer
(a) $v(t) = -\tan(t)$, $a(t) = -\sec^2(t)$

(b) The particle is **never** at rest on $0 < t < \dfrac{\pi}{2}$ because $v(t) = -\tan(t) \neq 0$ for all $t$ in $(0, \pi/2)$.

(c) $\dfrac{1}{2}\ln\!\left(\dfrac{3}{2}\right) \approx 0.203$

## Explanation
**(a)** The velocity is the first derivative of position:

$$v(t) = s'(t) = \frac{d}{dt}[\ln(\cos(t))] = \frac{1}{\cos(t)} \cdot (-\sin(t)) = -\tan(t)$$

The acceleration is the derivative of velocity:

$$a(t) = v'(t) = \frac{d}{dt}[-\tan(t)] = -\sec^2(t)$$

**(b)** The particle is at rest when $v(t) = 0$:

$$-\tan(t) = 0 \implies \tan(t) = 0 \implies t = 0$$

But $t = 0$ is **not** in the open interval $(0, \pi/2)$. For all $t \in (0, \pi/2)$, we have $\tan(t) > 0$, so $v(t) = -\tan(t) < 0$. The particle is **never at rest** on this interval; it is always moving in the negative direction.

**(c)** Since $v(t) = -\tan(t) < 0$ for all $t \in (0, \pi/2)$, the particle moves in one direction (negative) throughout the interval. When the particle doesn't change direction, total distance equals the absolute value of displacement:

$$\text{Total distance} = \left|\,s\!\left(\frac{\pi}{4}\right) - s\!\left(\frac{\pi}{6}\right)\,\right|$$

$$s\!\left(\frac{\pi}{4}\right) = \ln\!\left(\cos\frac{\pi}{4}\right) = \ln\!\left(\frac{\sqrt{2}}{2}\right)$$
$$s\!\left(\frac{\pi}{6}\right) = \ln\!\left(\cos\frac{\pi}{6}\right) = \ln\!\left(\frac{\sqrt{3}}{2}\right)$$

$$s\!\left(\frac{\pi}{4}\right) - s\!\left(\frac{\pi}{6}\right) = \ln\!\left(\frac{\sqrt{2}/2}{\sqrt{3}/2}\right) = \ln\!\left(\sqrt{\frac{2}{3}}\right) = \frac{1}{2}\ln\!\left(\frac{2}{3}\right)$$

Since this is negative:

$$\text{Total distance} = \left|\frac{1}{2}\ln\!\left(\frac{2}{3}\right)\right| = \frac{1}{2}\ln\!\left(\frac{3}{2}\right) \approx 0.203$$

Alternatively, integrating speed:

$$\text{Distance} = \int_{\pi/6}^{\pi/4} |v(t)|\,dt = \int_{\pi/6}^{\pi/4} \tan(t)\,dt = \Big[-\ln|\cos(t)|\Big]_{\pi/6}^{\pi/4}$$
$$= -\ln\!\left(\frac{\sqrt{2}}{2}\right) + \ln\!\left(\frac{\sqrt{3}}{2}\right) = \ln\!\left(\frac{\sqrt{3}/2}{\sqrt{2}/2}\right) = \ln\!\left(\sqrt{\frac{3}{2}}\right) = \frac{1}{2}\ln\!\left(\frac{3}{2}\right)$$

The total distance traveled is **$\dfrac{1}{2}\ln\!\left(\dfrac{3}{2}\right) \approx 0.203$**.
