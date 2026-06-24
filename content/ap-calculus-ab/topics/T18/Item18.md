---
id: T18-Item18
difficulty: C
calculator: calc
type: frq
---
A particle moves along the curve $y = \frac{8}{x^2 + 2}$ for $x \ge 0$. The particle's x-coordinate is increasing at a rate of 2 units per second.

(a) Find $\frac{dy}{dt}$ when $x = 2$.
(b) At the point where $y$ is maximized, what is $\frac{dy}{dt}$? Explain your reasoning.
(c) Is the particle approaching a horizontal asymptote as $x \to \infty$? Justify your answer using calculus.

## Answer
(a) $\frac{dy}{dt} = -\frac{16}{9}$ units per second

(b) $\frac{dy}{dt} = 0$ because at the maximum of $y$, $\frac{dy}{dx} = 0$, and by chain rule $\frac{dy}{dt} = \frac{dy}{dx} \cdot \frac{dx}{dt}$, so $\frac{dy}{dt} = 0 \cdot 2 = 0$.

(c) As $x \to \infty$, $y \to 0^+$. $y' = \frac{-16x}{(x^2+2)^2} < 0$ for $x > 0$, so $y$ is strictly decreasing and bounded below by 0. By the Monotonic Convergence Theorem (or since derivative is negative and approaches 0), $y$ approaches 0 as $x \to \infty$. The horizontal asymptote is $y = 0$.

## Explanation
(a) $y = 8(x^2+2)^{-1}$. $\frac{dy}{dx} = -8(x^2+2)^{-2} \cdot 2x = \frac{-16x}{(x^2+2)^2}$. At $x = 2$: $\frac{dy}{dx} = \frac{-32}{(4+2)^2} = \frac{-32}{36} = -\frac{8}{9}$. $\frac{dy}{dt} = \frac{dy}{dx} \cdot \frac{dx}{dt} = -\frac{8}{9} \cdot 2 = -\frac{16}{9}$.

(b) $y = 8(x^2+2)^{-1}$. Maximum at $x=0$ (since for $x>0$, $y$ decreases as $x$ increases). At $x=0$, $\frac{dy}{dx} = 0$. $\frac{dy}{dt} = 0 \cdot 2 = 0$.

(c) $\lim_{x \to \infty} y = 0$. $y' < 0$ for $x > 0$, so $y$ is strictly decreasing. Since $y > 0$ and bounded below, and decreasing, $\lim_{x \to \infty} y$ exists. At the limit, $y' \to 0$. The horizontal asymptote is $y = 0$.
