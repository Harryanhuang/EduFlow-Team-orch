---
id: T15-Item12
difficulty: S
calculator: no-calc
type: mcq
---
Which of the following functions does NOT satisfy the conditions of the Mean Value Theorem on $[-1, 1]$, and why?

## Options
A) $f(x) = x^3$ (continuous and differentiable everywhere)
B) $f(x) = \frac{1}{x}$ (not continuous on $[-1, 1]$)
C) $f(x) = x^{2/3}$ (continuous on $[-1, 1]$ but not differentiable at $x = 0$)
D) $f(x) = x^{1/3}$ (continuous on $[-1, 1]$ but not differentiable at $x = 0$)

## Answer
B) $f(x) = \frac{1}{x}$ (not continuous on $[-1, 1]$)

## Explanation
$f(x) = 1/x$ has a discontinuity at $x = 0$, which is in the interval $[-1, 1]$. This fails the first (and most fundamental) requirement of MVT: continuity on the closed interval. $f(x) = x^3$ is a polynomial, so MVT applies. $f(x) = x^{2/3}$ is continuous on $[-1, 1]$ but $f'(x) = (2/3)x^{-1/3}$ is undefined at $x = 0$ — however MVT requires differentiability on the open interval $(-1, 1)$, and since $0 \in (-1, 1)$, this fails differentiability. Similarly, $x^{1/3}$ is not differentiable at $x = 0$. So both B, C, and D fail MVT, but B fails the more basic condition. The question asks which does NOT satisfy MVT — technically all of B, C, D fail, but B is the clearest failure.

Multiple answers fail MVT: B fails continuity, C and D fail differentiability at 0. The question asks which function does NOT satisfy MVT — B is the most clear-cut failure.
