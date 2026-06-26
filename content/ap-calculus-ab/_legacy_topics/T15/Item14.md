---
id: T15-Item14
difficulty: C
calculator: calc
type: frq
---
Let $f(x) = x^3 - 3kx^2 + 4$, where $k$ is a constant. For each value of $k$ below, determine the absolute maximum and absolute minimum of $f$ on the interval $[0, 4]$, or state that the Extreme Value Theorem does not apply.

(a) $k = 0$
(b) $k = 2$
(c) $k = 3$
(d) In general, for what values of $k$ does the Extreme Value Theorem apply to $f$ on $[0, 4]$? Explain.

## Answer
(a) $k = 0$: $f(x) = x^3 + 4$. $f'(x) = 3x^2$, critical point at $x = 0$. $f(0) = 4$, $f(4) = 68$. Absolute minimum: $4$ at $x = 0$. Absolute maximum: $68$ at $x = 4$.
(b) $k = 2$: $f(x) = x^3 - 12x^2 + 4$. $f'(x) = 3x^2 - 24x = 3x(x - 8)$, critical points at $x = 0$ and $x = 8$ (8 not in [0,4]). $f(0) = 4$, $f(4) = 64 - 192 + 4 = -124$. Absolute minimum: $-124$ at $x = 4$. Absolute maximum: $4$ at $x = 0$.
(c) $k = 3$: $f(x) = x^3 - 27x^2 + 4$. $f'(x) = 3x^2 - 54x = 3x(x - 18)$, critical point at $x = 0$ (18 not in [0,4]). $f(0) = 4$, $f(4) = 64 - 432 + 4 = -364$. Absolute minimum: $-364$ at $x = 4$. Absolute maximum: $4$ at $x = 0$.
(d) The Extreme Value Theorem always applies since $f$ is a polynomial (hence continuous) on the closed interval $[0, 4]$, regardless of the value of $k$. No restriction on $k$.

## Explanation
Since $f(x) = x^3 - 3kx^2 + 4$ is a polynomial for all real $k$, it is continuous everywhere. By the EVT, it attains absolute extrema on any closed bounded interval $[0, 4]$ for all real $k$. The critical points depend on $k$: $f'(x) = 3x(x - 2k) = 0$, giving $x = 0$ and $x = 2k$. The nature of the absolute extrema varies with $k$.
