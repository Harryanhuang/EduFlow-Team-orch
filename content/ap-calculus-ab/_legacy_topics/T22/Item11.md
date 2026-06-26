---
id: T22-Item11
difficulty: S
calculator: calc
type: mcq
---
Which of the following is the solution to the initial value problem \(\dfrac{dy}{dx} + 2y = 6\) with \(y(0) = 1\)?

A) \(y = 3 - 2e^{-2x}\)
B) \(y = 3 + 2e^{-2x}\)
C) \(y = 3 - 2e^{2x}\)
D) \(y = 3 + 2e^{2x}\)

## Answer
A

## Explanation
This is a first-order linear differential equation: \(\frac{dy}{dx} + 2y = 6\).
The integrating factor is \(\mu(x) = e^{\int 2\,dx} = e^{2x}\).
Multiply through:
\[e^{2x}\frac{dy}{dx} + 2e^{2x}y = 6e^{2x}\]
\[\frac{d}{dx}(e^{2x}y) = 6e^{2x}\]
Integrate:
\[e^{2x}y = \int 6e^{2x}\,dx = 3e^{2x} + C\]
\[y = 3 + Ce^{-2x}\]
Apply \(y(0) = 1\):
\[1 = 3 + C \implies C = -2\]
So \(y = 3 - 2e^{-2x}\), which is option A.
