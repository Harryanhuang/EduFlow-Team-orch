---
id: T22-Item10
difficulty: S
calculator: calc
type: frq
---
Use separation of variables to find the general solution of \(\dfrac{dy}{dx} = 2y(3 - y)\).

## Answer
Separate the variables:
\[\frac{dy}{dx} = 2y(3-y) \implies \frac{dy}{y(3-y)} = 2\,dx\]
Use partial fractions on the left:
\[\frac{1}{y(3-y)} = \frac{A}{y} + \frac{B}{3-y}\]
\[1 = A(3-y) + By\]
Setting \(y = 0\): \(1 = 3A \implies A = \frac{1}{3}\).
Setting \(y = 3\): \(1 = 3B \implies B = \frac{1}{3}\).
So:
\[\int \left(\frac{1/3}{y} + \frac{1/3}{3-y}\right)dy = \int 2\,dx\]
\[\frac{1}{3}\ln|y| - \frac{1}{3}\ln|3-y| = 2x + C\]
Multiply by 3:
\[\ln\left|\frac{y}{3-y}\right| = 6x + 3C\]
\[\frac{y}{3-y} = Ce^{6x}\]
Solve for \(y\):
\[y = Ce^{6x}(3-y) \implies y = 3Ce^{6x} - Ce^{6x}y \implies y(1+Ce^{6x}) = 3Ce^{6x}\]
\[y = \frac{3Ce^{6x}}{1+Ce^{6x}} = \frac{3}{e^{-6x}+C}\]
Equivalently:
\[\frac{y}{3-y} = Ce^{6x}\]
This is the general implicit solution.

## Explanation
The right-hand side \(2y(3-y)\) is a logistic-type expression. Separating and using partial fractions yields \(\ln\left|\frac{y}{3-y}\right| = 6x + C\), which can be algebraically solved for \(y\).
