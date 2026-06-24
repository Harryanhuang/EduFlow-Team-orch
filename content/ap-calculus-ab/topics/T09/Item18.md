---
id: T09-Item18
difficulty: C
calculator: calc
type: frq
---
Let $y = (x^2 + 1)^{\sin(x)}$.

(a) Use logarithmic differentiation to find $\dfrac{dy}{dx}$.

(b) Evaluate $\dfrac{dy}{dx}$ at $x = \dfrac{\pi}{2}$.

(c) Find the equation of the tangent line to the curve at $x = \dfrac{\pi}{2}$.

## Answer
(a) $\dfrac{dy}{dx} = (x^2 + 1)^{\sin(x)}\left[\cos(x)\,\ln(x^2 + 1) + \dfrac{2x\sin(x)}{x^2 + 1}\right]$

(b) $\dfrac{dy}{dx}\Big|_{x = \pi/2} = \pi$

(c) $y = \pi x - \dfrac{\pi^2}{4} + 1$

## Explanation
**(a)** Take the natural logarithm of both sides:

$$\ln(y) = \ln\!\left[(x^2 + 1)^{\sin(x)}\right] = \sin(x)\,\ln(x^2 + 1)$$

Differentiate both sides with respect to $x$ using the **product rule** on the right side:

$$\frac{1}{y}\cdot\frac{dy}{dx} = \cos(x)\,\ln(x^2 + 1) + \sin(x) \cdot \frac{1}{x^2 + 1} \cdot 2x$$

Multiply both sides by $y = (x^2 + 1)^{\sin(x)}$:

$$\frac{dy}{dx} = (x^2 + 1)^{\sin(x)}\left[\cos(x)\,\ln(x^2 + 1) + \frac{2x\sin(x)}{x^2 + 1}\right]$$

**(b)** At $x = \dfrac{\pi}{2}$:

- $\sin(\pi/2) = 1$
- $\cos(\pi/2) = 0$
- $x^2 + 1 = \dfrac{\pi^2}{4} + 1$

$$\frac{dy}{dx}\Big|_{x = \pi/2} = \left(\frac{\pi^2}{4} + 1\right)^1 \left[0 \cdot \ln\!\left(\frac{\pi^2}{4} + 1\right) + \frac{2 \cdot (\pi/2) \cdot 1}{\pi^2/4 + 1}\right]$$
$$= \left(\frac{\pi^2}{4} + 1\right) \cdot \left[0 + \frac{\pi}{\pi^2/4 + 1}\right]$$
$$= \left(\frac{\pi^2}{4} + 1\right) \cdot \frac{\pi}{\pi^2/4 + 1} = \pi$$

**(c)** The point of tangency:

$$y\!\left(\frac{\pi}{2}\right) = \left(\frac{\pi^2}{4} + 1\right)^{\sin(\pi/2)} = \frac{\pi^2}{4} + 1$$

The tangent line has slope $m = \pi$ and passes through $\left(\dfrac{\pi}{2},\;\dfrac{\pi^2}{4} + 1\right)$:

$$y - \left(\frac{\pi^2}{4} + 1\right) = \pi\left(x - \frac{\pi}{2}\right)$$
$$y = \pi x - \frac{\pi^2}{2} + \frac{\pi^2}{4} + 1$$
$$y = \pi x - \frac{\pi^2}{4} + 1$$

The tangent line is **$y = \pi x - \dfrac{\pi^2}{4} + 1$**.
