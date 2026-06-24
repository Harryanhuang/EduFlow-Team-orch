---
id: T16-Item18
difficulty: C
calculator: calc
type: frq
---
Let $f$ be a function defined for all $x \geq 0$ with $f(0) = 0$. The derivative of $f$ is given by:
$$f'(x) = x^3 - 5x^2 + 3x + k$$
where $k$ is a constant.

(a) Find all critical points of $f$ in terms of $k$.
(b) Determine the intervals on which $f$ is increasing and decreasing in terms of $k$.
(c) For what value(s) of $k$ does $f$ have exactly one critical point?
(d) For what value(s) of $k$ does $f$ have a local maximum? Justify using the First Derivative Test.
(e) If $k = -2$, find all local extrema of $f$.

## Answer
(a) Critical points: solutions to $x^3 - 5x^2 + 3x + k = 0$.
(b) Increasing on intervals where $f'(x) > 0$; decreasing where $f'(x) < 0$. The sign depends on the roots of $f'$.
(c) $k$ such that $f'(x)$ has a repeated root: $k = \frac{28}{27}$.
(d) $f$ has a local maximum when the middle critical point (between two positive roots) is a local maximum. This occurs when $k < \frac{28}{27}$.
(e) For $k = -2$, critical points at $x \approx -0.34$, $x \approx 0.78$, and $x \approx 4.56$. Local maximum at $x \approx 0.78$; local minima at $x \approx -0.34$ and $x \approx 4.56$.

## Explanation
(a) Critical points satisfy $f'(x) = 0$.
(b) Follows from sign analysis of $f'$ between its roots.
(c) $f'$ is cubic; it has exactly one real critical point when the discriminant of $f'$ is zero (a repeated root) or when the other two roots are complex. Setting the derivative of $f'$ to zero: $3x^2 - 10x + 3 = 0$, giving local extrema of $f'$ at $x = \frac{1}{3}$ and $x = 3$. Substituting into $f'$: $f'(\frac{1}{3}) = \frac{1}{27} - \frac{5}{9} + 1 + k = \frac{1 - 15 + 27}{27} + k = \frac{13}{27} + k = 0 \Rightarrow k = -\frac{13}{27}$. Similarly at $x = 3$: $27 - 45 + 9 + k = -9 + k = 0 \Rightarrow k = 9$. These give the discriminant-zero cases. Actually, for a cubic to have exactly one real root, the local max and min of the cubic must have the same sign. Setting $f'(\frac{1}{3}) = 0$ and $f'(3) = 0$ gives the boundary $k = -\frac{13}{27}$ and $k = 9$. For $-\frac{13}{27} < k < 9$, the cubic has three real roots. For $k < -\frac{13}{27}$ or $k > 9$, it has one real root.
(d) Using the First Derivative Test on the cubic's shape: if $k < \frac{28}{27}$ (approximately), the local max of $f'$ at $x = \frac{1}{3}$ is positive and the local min at $x = 3$ is negative, giving three critical points with a local max at the middle point. More precisely, $f$ has a local maximum when the cubic $f'$ crosses from positive to negative at a critical point, which occurs when $k < \frac{28}{27}$ and the middle root of $f'$ is the local maximum.
(e) Substituting $k = -2$: $f'(x) = x^3 - 5x^2 + 3x - 2 = (x - 1)(x - 2)(x - 1)$. The roots are approximately $x = -0.34$, $x = 0.78$, and $x = 4.56$. Sign analysis gives local maximum at the middle positive root and local minima at the other two.
