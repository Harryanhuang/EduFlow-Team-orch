---
id: T09-Item17
difficulty: C
calculator: no-calc
type: frq
---
The temperature (in degrees Fahrenheit) of a cooling object at time $t$ minutes is modeled by:

$$T(t) = 70 + 30\,e^{-0.1t}\cos(t)$$

(a) Find $T'(t)$.

(b) At what rate is the temperature changing at $t = 5$ minutes? Express your answer in degrees Fahrenheit per minute. You may leave your answer in exact form or round to three decimal places.

(c) Is the temperature increasing or decreasing at $t = 5$? Justify your answer.

## Answer
(a) $T'(t) = 30\,e^{-0.1t}[-0.1\cos(t) - \sin(t)]$

(b) $T'(5) \approx 16.933$ degrees Fahrenheit per minute

(c) The temperature is **increasing** at $t = 5$ because $T'(5) > 0$.

## Explanation
**(a)** Apply the product rule to $30\,e^{-0.1t}\cos(t)$:

$$T'(t) = 30 \cdot \frac{d}{dt}[e^{-0.1t}\cos(t)]$$
$$= 30\left[\frac{d}{dt}(e^{-0.1t}) \cdot \cos(t) + e^{-0.1t} \cdot \frac{d}{dt}(\cos(t))\right]$$
$$= 30\left[(-0.1\,e^{-0.1t})\cos(t) + e^{-0.1t}(-\sin(t))\right]$$
$$= 30\,e^{-0.1t}[-0.1\cos(t) - \sin(t)]$$

**(b)** Evaluate at $t = 5$:

$$T'(5) = 30\,e^{-0.5}[-0.1\cos(5) - \sin(5)]$$

Note: $5$ radians $\approx 286.5^\circ$, which is in the fourth quadrant, so $\cos(5) > 0$ and $\sin(5) < 0$.

Numerically:
- $e^{-0.5} \approx 0.60653$
- $\cos(5) \approx 0.28366$
- $\sin(5) \approx -0.95892$

$$-0.1\cos(5) - \sin(5) \approx -0.02837 + 0.95892 \approx 0.93056$$

$$T'(5) \approx 30 \cdot 0.60653 \cdot 0.93056 \approx 16.933$$

**Answer: $T'(5) \approx 16.933$ degrees Fahrenheit per minute.**

**(c)** Since $T'(5) \approx 16.933 > 0$, the temperature is **increasing** at $t = 5$ minutes.

The reason the temperature is increasing despite the exponential decay factor is that the cosine term causes oscillation. At $t = 5$ (fourth quadrant), $\sin(5) < 0$, and the $-\sin(5)$ term in $T'(t)$ dominates the $-0.1\cos(5)$ term, making the overall derivative positive. The temperature oscillates around $70^\circ\text{F}$ (room temperature) with a decaying amplitude, so it can be increasing at certain times even though the envelope is shrinking.
