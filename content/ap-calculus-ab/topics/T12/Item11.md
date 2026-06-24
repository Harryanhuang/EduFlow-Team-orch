---
id: T12-Item11
difficulty: S
calculator: no-calc
type: frq
---
The temperature $T(h)$ in degrees Fahrenheit of a city on a summer day is modeled by $T(h) = 72 + 12\sin\left(\frac{\pi(h - 8)}{12}\right)$ for $6 \leq h \leq 20$, where $h$ is the number of hours after midnight.

(a) Find the rate at which the temperature is changing at $h = 10$ (10:00 AM). Include units.
(b) Is the temperature increasing or decreasing at $h = 16$ (4:00 PM)? Justify your answer.
(c) At what time $h$ is the temperature changing most rapidly?

## Answer
(a) $T'(h) = 12 \cdot \frac{\pi}{12} \cos\left(\frac{\pi(h-8)}{12}\right) = \pi\cos\left(\frac{\pi(h-8)}{12}\right)$. At $h = 10$: $T'(10) = \pi\cos\left(\frac{\pi}{6}\right) = \pi \cdot \frac{\sqrt{3}}{2} \approx 2.72$ degrees Fahrenheit per hour.

(b) $T'(16) = \pi\cos\left(\frac{8\pi}{12}\right) = \pi\cos\left(\frac{2\pi}{3}\right) = \pi \cdot \left(-\frac{1}{2}\right) = -\frac{\pi}{2} \approx -1.57$. Since $T'(16) < 0$, the temperature is decreasing at 4:00 PM.

(c) The temperature changes most rapidly when $|T'(h)|$ is maximized. Since $T'(h) = \pi\cos\left(\frac{\pi(h-8)}{12}\right)$, the maximum absolute value is $\pi$, occurring when $\cos\left(\frac{\pi(h-8)}{12}\right) = \pm 1$. On $[6, 20]$: $\frac{\pi(h-8)}{12} = 0 \Rightarrow h = 8$ (maximum rate of increase, $T'(8) = \pi$), and $\frac{\pi(h-8)}{12} = \pi \Rightarrow h = 20$ (maximum rate of decrease, $T'(20) = -\pi$). So the temperature changes most rapidly at $h = 8$ (increasing) and $h = 20$ (decreasing).

## Explanation
Part (a) tests chain rule with units. Part (b) tests sign interpretation of the derivative. Part (c) requires recognizing that "most rapidly" means maximizing the absolute value of the derivative, not finding where the derivative is zero.
