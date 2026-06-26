---
id: T07-Item10
difficulty: S
calculator: no-calc
type: frq
---
Find the equation of the tangent line to $y = \dfrac{\tan x}{x}$ at $x = \frac{\pi}{4}$.

## Answer
$y = \dfrac{8(\pi - 2)}{\pi^2}\left(x - \frac{\pi}{4}\right) + \dfrac{4}{\pi}$

## Explanation
First, find the point: at $x = \frac{\pi}{4}$, $y = \frac{\tan(\pi/4)}{\pi/4} = \frac{1}{\pi/4} = \frac{4}{\pi}$.

Using the quotient rule with $u = \tan x$, $v = x$, $u' = \sec^2 x$, $v' = 1$:
$f'(x) = \frac{\sec^2 x \cdot x - \tan x}{x^2}$.

At $x = \frac{\pi}{4}$: $\sec^2(\pi/4) = 2$, $\tan(\pi/4) = 1$.
$f'(\pi/4) = \frac{2 \cdot \frac{\pi}{4} - 1}{\left(\frac{\pi}{4}\right)^2} = \frac{\frac{\pi}{2} - 1}{\frac{\pi^2}{16}} = \frac{16\left(\frac{\pi}{2} - 1\right)}{\pi^2} = \frac{8\pi - 16}{\pi^2} = \frac{8(\pi - 2)}{\pi^2}$.

Tangent line: $y - \frac{4}{\pi} = \frac{8(\pi - 2)}{\pi^2}\left(x - \frac{\pi}{4}\right)$.
