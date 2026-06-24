---
id: T14-Item11
difficulty: S
calculator: no-calc
type: mcq
---
Evaluate $\displaystyle \lim_{x \to 0} \frac{\tan x - x}{x^3}$.

## Options
A) $\dfrac{1}{3}$
B) $\dfrac{1}{2}$
C) 1
D) $\dfrac{1}{6}$

## Answer
A) $\dfrac{1}{3}$

## Explanation
This is 0/0. Apply L'Hôpital's Rule three times:
1. $\displaystyle \lim_{x \to 0} \frac{\sec^2 x - 1}{3x^2} = \lim_{x \to 0} \frac{\tan^2 x}{3x^2}$ (since $\sec^2 x - 1 = \tan^2 x$)
2. $\displaystyle \lim_{x \to 0} \frac{2\tan x \sec^2 x}{6x} = \lim_{x \to 0} \frac{\tan x \sec^2 x}{3x}$
3. $\displaystyle \lim_{x \to 0} \frac{\sec^4 x + 2\tan^2 x \sec^2 x}{3} = \frac{1}{3}$
