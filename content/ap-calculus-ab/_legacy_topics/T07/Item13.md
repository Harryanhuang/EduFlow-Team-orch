---
id: T07-Item13
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = x^2 \cot x$.

(a) Find $f'(x)$.
(b) Find the equation of the normal line to $f$ at $x = \frac{\pi}{4}$.
(c) For what values of $x$ in $(0, \pi)$ is $f'(x) = -x^2$?

## Answer
(a) Using the product rule: $f'(x) = 2x \cot x + x^2(-\csc^2 x) = 2x \cot x - x^2 \csc^2 x$.

(b) At $x = \frac{\pi}{4}$: $\cot(\frac{\pi}{4}) = 1$, $f(\frac{\pi}{4}) = \frac{\pi^2}{16}$.

$f'(\frac{\pi}{4}) = 2 \cdot \frac{\pi}{4} \cdot 1 - \frac{\pi^2}{16} \cdot (\sqrt{2})^2 = \frac{\pi}{2} - \frac{\pi^2}{8}$.

Slope of normal: $m_n = \dfrac{-1}{\frac{\pi}{2} - \frac{\pi^2}{8}} = \dfrac{-8}{4\pi - \pi^2} = \dfrac{-8}{\pi(4 - \pi)}$.

Normal line: $y - \frac{\pi^2}{16} = \dfrac{-8}{\pi(4 - \pi)}\left(x - \frac{\pi}{4}\right)$.

(c) Set $f'(x) = -x^2$: $2x \cot x - x^2 \csc^2 x = -x^2$.

For $x \neq 0$: $2 \cot x - x \csc^2 x = -x$.

$2 \cot x = x(\csc^2 x - 1) = x \cot^2 x$.

For $\cot x \neq 0$: $x = \dfrac{2}{\cot x} = 2 \tan x$.

The equation $\tan x = \frac{x}{2}$ has a solution in $(0, \frac{\pi}{2})$ approximately $x \approx 1.1656$. Also check $\cot x = 0$ at $x = \frac{\pi}{2}$: $0 - \frac{\pi^2}{4} \cdot 1 \neq -\frac{\pi^2}{4}$. Yes, at $x = \frac{\pi}{2}$: LHS = $-\frac{\pi^2}{4}$ = RHS = $-\frac{\pi^2}{4}$. So $x = \frac{\pi}{2}$ is also a solution.

## Explanation
This is a multi-step problem combining the product rule with cotangent, normal line equations, and solving a transcendental equation. Part (c) requires algebraic manipulation using the identity $\csc^2 x - 1 = \cot^2 x$.
