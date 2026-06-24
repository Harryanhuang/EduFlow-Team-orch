---
id: T22-Item14
difficulty: C
calculator: calc
type: frq
---
Consider the differential equation \(\dfrac{dy}{dx} = y^{2} - 4\).

**(a)** Find all equilibrium solutions (constant solutions) and classify each as stable or unstable.

**(b)** Sketch a slope field for the differential equation. Identify the behavior of solutions in the regions \(y < -2\), \(-2 < y < 2\), and \(y > 2\).

**(c)** Solve the differential equation using separation of variables.

**(d)** If \(y(0) = 1\), find the particular solution and determine \(\displaystyle\lim_{x\to\infty} y(x)\).

## Answer
**(a)** Set \(\frac{dy}{dx} = 0\): \(y^{2} - 4 = 0 \implies y = \pm 2\).
For \(y = 2\): if \(y$ is slightly above 2, \(y' = y^{2}-4 > 0\) (increasing away); if slightly below 2, \(y' < 0\) (decreasing toward 2). So \(y = 2\) is **unstable**.
For \(y = -2\): if slightly above -2, \(y' < 0\) (decreasing back); if slightly below, \(y' > 0\) (increasing back). So \(y = -2\) is **stable**.

**(b)** For \(y > 2\): \(y^{2} - 4 > 0\), so \(y' > 0$ and solutions increase toward \(+\infty\).
For \(-2 < y < 2\): \(y^{2} - 4 < 0\), so \(y' < 0\) and solutions decrease toward \(-2\).
For \(y < -2\): \(y^{2} - 4 > 0\), so \(y' > 0\) and solutions increase toward \(-2\).

**(c)** Separate:
\[\frac{dy}{y^{2}-4} = dx\]
Factor: \(y^{2}-4 = (y-2)(y+2)\). Partial fractions:
\[\frac{1}{(y-2)(y+2)} = \frac{A}{y-2} + \frac{B}{y+2}\]
\[1 = A(y+2) + B(y-2)\]
Setting \(y = 2\): \(1 = 4A \implies A = \frac{1}{4}\).
Setting \(y = -2\): \(1 = -4B \implies B = -\frac{1}{4}\).
So:
\[\int \left(\frac{1/4}{y-2} - \frac{1/4}{y+2}\right)dy = \int dx\]
\[\frac{1}{4}\ln|y-2| - \frac{1}{4}\ln|y+2| = x + C\]
\[\ln\left|\frac{y-2}{y+2}\right| = 4x + 4C\]
\[\frac{y-2}{y+2} = Ce^{4x}\]
\[y-2 = Ce^{4x}(y+2) \implies y(1-Ce^{4x}) = 2 + 2Ce^{4x}\]
\[y = \frac{2(1+Ce^{4x})}{1-Ce^{4x}}\]

**(d)** For \(y(0) = 1\):
\[\frac{1-2}{1+2} = \frac{-1}{3} = Ce^{0} \implies C = -\frac{1}{3}\]
\[y(x) = \frac{2(1-\frac{1}{3}e^{4x})}{1+\frac{1}{3}e^{4x}} = \frac{2(3-e^{4x})}{3+e^{4x}}\]
As \(x \to \infty\), \(e^{4x} \to \infty\) and \(y(x) \to \frac{2(0-\infty)}{0+\infty} \to -2\).
So \(\displaystyle\lim_{x\to\infty} y(x) = -2\). This matches the stability analysis: the solution in \(-2 < y < 2\) decreases asymptotically toward the stable equilibrium \(y = -2\).

## Explanation
Parts (a)-(b) require qualitative analysis of the autonomous equation. Part (c) uses partial fractions to integrate. Part (d) confirms that the analytical solution agrees with the slope field behavior.
