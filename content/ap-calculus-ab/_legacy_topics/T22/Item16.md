---
id: T22-Item16
difficulty: C
calculator: calc
type: mcq
---
Which of the following is the particular solution to \(\dfrac{dy}{dx} = 3x^{2}y\) with \(y(0) = 2\)?

A) \(y = 2e^{x^{3}}\)
B) \(y = 2e^{3x^{3}}\)
C) \(y = e^{x^{3}} + 1\)
D) \(y = 2e^{x^{3}/3}\)

## Answer
A

## Explanation
Separate variables:
\[\frac{dy}{y} = 3x^{2}\,dx\]
Integrate:
\[\ln|y| = x^{3} + C\]
\[y = Ae^{x^{3}}\]
Apply \(y(0) = 2\): \(2 = A \cdot e^{0} = A\), so \(y = 2e^{x^{3}}\).

Option B gives \(y = 2e^{3x^{3}}\), which would come from \(\frac{dy}{y} = 9x^{2}\,dx\). Option C does not satisfy the initial condition. Option D gives \(y = 2e^{x^{3}/3}\), which would come from \(\frac{dy}{y} = x^{2}\,dx\).
