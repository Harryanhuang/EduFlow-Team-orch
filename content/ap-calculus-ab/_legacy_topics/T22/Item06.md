---
id: T22-Item06
difficulty: S
calculator: calc
type: mcq
---
Which of the following is the general solution to \(\dfrac{dy}{dx} = 3y\)?

A) \(y = Ce^{3x}\)
B) \(y = Ce^{x/3}\)
C) \(y = Cx^{3}\)
D) \(y = 3e^{x} + C\)

## Answer
A

## Explanation
This is a separable differential equation. Rewrite as \(\frac{1}{y}\,dy = 3\,dx\) and integrate:
\[\int \frac{1}{y}\,dy = \int 3\,dx\]
\[\ln|y| = 3x + C\]
\[|y| = e^{3x+C} = e^{C}e^{3x}\]
Letting \(C\) absorb the absolute value gives \(y = Ce^{3x}\), where \(C\) can be any real constant (positive or negative, since \(|y| = e^{3x+C}\) and \(y = \pm e^{C}e^{3x}\) both collapse to the single constant form).
