---
id: T07-Item18
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{x}{\sin x} + \cos x$ for $0 < x < \frac{\pi}{2}$.

(a) Find $f'(x)$.
(b) Find the equation of the tangent line to the graph of $f$ at $x = \frac{\pi}{4}$.
(c) Find all critical points of $f$ in the interval $(0, \frac{\pi}{2})$.
(d) For what value(s) of $x$ in $(0, \frac{\pi}{2})$ is the tangent line to $f$ horizontal?

## Answer
(a) Using the quotient rule on the first term and standard trig derivatives on the second:

$f'(x) = \dfrac{1 \cdot \sin x - x \cdot \cos x}{\sin^2 x} - \sin x = \dfrac{\sin x - x \cos x}{\sin^2 x} - \sin x$.

(b) At $x = \frac{\pi}{4}$:

$f(\frac{\pi}{4}) = \dfrac{\pi/4}{\sqrt{2}/2} + \frac{\sqrt{2}}{2} = \frac{\pi}{2\sqrt{2}} + \frac{\sqrt{2}}{2} = \frac{\pi + 2}{2\sqrt{2}}$.

$f'(\frac{\pi}{4}) = \dfrac{\frac{\sqrt{2}}{2} - \frac{\pi}{4} \cdot \frac{\sqrt{2}}{2}}{\frac{1}{2}} - \frac{\sqrt{2}}{2} = \sqrt{2} - \frac{\pi\sqrt{2}}{4} - \frac{\sqrt{2}}{2} = \frac{\sqrt{2}}{2} - \frac{\pi\sqrt{2}}{4}$.

Tangent line: $y - \frac{\pi + 2}{2\sqrt{2}} = \left(\frac{\sqrt{2}}{2} - \frac{\pi\sqrt{2}}{4}\right)\left(x - \frac{\pi}{4}\right)$.

(c) Critical points occur where $f'(x) = 0$:

$\dfrac{\sin x - x \cos x}{\sin^2 x} - \sin x = 0$

$\sin x - x \cos x = \sin^3 x$

$x \cos x = \sin x - \sin^3 x = \sin x(1 - \sin^2 x) = \sin x \cos^2 x$

$x = \sin x \cos x = \frac{1}{2}\sin(2x)$.

This transcendental equation has no closed-form solution in $(0, \frac{\pi}{2})$. The only solution is $x = 0$ (not in the open interval), so there are no critical points in $(0, \frac{\pi}{2})$.

(d) No horizontal tangent exists in $(0, \frac{\pi}{2})$ since the only solution to $f'(x) = 0$ is $x = 0$, which is not in the open interval.

## Explanation
This multi-part FRQ combines the quotient rule, trig derivatives, tangent/normal lines, and critical point analysis. Part (c) requires recognizing a transcendental equation and reasoning about its solutions within a given interval.
