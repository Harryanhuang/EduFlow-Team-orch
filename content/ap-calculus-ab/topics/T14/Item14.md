---
id: T14-Item14
difficulty: C
calculator: calc
type: frq
---
A spherical balloon has volume $V = \dfrac{4}{3}\pi r^3$ cm$^3$. When the radius is $r = 5$ cm, the volume is $V(5) \approx 523.6$ cm$^3$.

(a) Find the linearization $L(r)$ of $V$ at $r = 5$.
(b) Use $L(r)$ to estimate the volume when the radius is $r = 5.2$ cm.
(c) Determine whether the approximation in part (b) is an overestimate or underestimate. Justify using the second derivative of $V$.
(d) The actual volume at $r = 5.2$ cm is approximately $588.9$ cm$^3$. Find the absolute approximation error and express it as a percentage of the actual volume.

## Answer
(a) $L(r) = \dfrac{500\pi}{3} + 100\pi(r - 5)$
(b) $L(5.2) = \dfrac{560\pi}{3} \approx 586.4$ cm$^3$
(c) Underestimate. Since $V''(r) = 8\pi r > 0$ for $r > 0$, the volume function is concave up. A tangent line to a concave-up curve lies below the curve, so $L(5.2) < V(5.2)$. The approximation underestimates.
(d) Error $\approx |588.9 - 586.4| = 2.5$ cm$^3$. Percentage error $\approx \dfrac{2.5}{588.9} \times 100\% \approx 0.42\%$.

## Explanation
(a) $V(5) = \frac{4}{3}\pi(125) = \frac{500\pi}{3} \approx 523.6$. $V'(r) = 4\pi r^2$, so $V'(5) = 100\pi$. Thus $L(r) = \frac{500\pi}{3} + 100\pi(r - 5)$.
(b) $L(5.2) = \frac{500\pi}{3} + 100\pi(0.2) = \frac{500\pi + 60\pi}{3} = \frac{560\pi}{3} \approx 586.4$ cm$^3$.
(c) Concavity: $V''(r) = 8\pi r > 0$ for $r > 0$, so $V$ is concave up and the tangent line lies below the curve, giving an underestimate.
(d) Actual $V(5.2) = \frac{4}{3}\pi(140.608) \approx 588.9$ cm$^3$. Error $\approx 2.5$ cm$^3$, or $\approx 0.42\%$ of the actual volume.
