---
id: T22-Item07
difficulty: S
calculator: calc
type: frq
---
Solve the differential equation \(\dfrac{dy}{dx} = \dfrac{x}{y}\) with the initial condition \(y(0) = -2\).

## Answer
Separate the variables:
\[\frac{dy}{dx} = \frac{x}{y} \implies y\,dy = x\,dx\]
Integrate both sides:
\[\int y\,dy = \int x\,dx\]
\[\frac{y^{2}}{2} = \frac{x^{2}}{2} + C\]
Multiply by 2:
\[y^{2} = x^{2} + 2C\]
Write as \(y^{2} = x^{2} + K\) where \(K = 2C\).

Apply \(y(0) = -2\):
\[(-2)^{2} = 0 + K \implies K = 4\]
So \(y^{2} = x^{2} + 4\).

Since \(y(0) = -2 < 0\), we take the negative branch:
\[y = -\sqrt{x^{2} + 4}\]

## Explanation
Separation gives \(y\,dy = x\,dx\). Integrating yields \(y^{2} = x^{2} + K\). The initial condition determines \(K = 4\), and the sign of \(y\) at \(x = 0\) selects the appropriate branch.
