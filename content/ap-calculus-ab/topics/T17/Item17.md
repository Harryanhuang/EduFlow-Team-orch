---
id: T17-Item17
difficulty: C
calculator: no-calc
type: frq
---
Consider the function $g(x) = \ln(x^2 + 1)$.

**(a)** Find $g'(x)$ and $g''(x)$. State the domain of $g$.

**(b)** Determine the intervals on which $g$ is increasing and decreasing.

**(c)** Determine the intervals on which $g$ is concave up and concave down.

**(d)** Find all local extrema and points of inflection. Justify using appropriate tests.

**(e)** Sketch $g(x)$, showing all features found in parts (a)-(d).

## Answer
**(a)**
Domain of $g$: $x^2 + 1 > 0$ for all $x$, so domain is all real numbers.

$g'(x) = \frac{2x}{x^2 + 1}$

$g''(x) = \frac{2(x^2 + 1) - 2x(2x)}{(x^2 + 1)^2} = \frac{2x^2 + 2 - 4x^2}{(x^2 + 1)^2} = \frac{2 - 2x^2}{(x^2 + 1)^2} = \frac{2(1 - x^2)}{(x^2 + 1)^2}$

**(b)**
$g'(x) = 0$ when $x = 0$.
$g'(x) > 0$ when $x > 0$ (since $x^2 + 1 > 0$) → increasing on $(0, \infty)$
$g'(x) < 0$ when $x < 0$ → decreasing on $(-\infty, 0)$

**(c)**
$g''(x) = 0$ when $1 - x^2 = 0$, so $x = \pm 1$.

Sign analysis:
- For $|x| > 1$: $1 - x^2 < 0$ → $g''(x) < 0$ (concave down)
- For $|x| < 1$: $1 - x^2 > 0$ → $g''(x) > 0$ (concave up)

So concave up on $(-1, 1)$, concave down on $(-\infty, -1) \cup (1, \infty)$.

**(d)**
Local extrema: At $x = 0$, $g'(0) = 0$ and $g''(0) = 2 > 0$, so by the Second Derivative Test, there's a local minimum at $x = 0$. $g(0) = \ln(1) = 0$.

Points of inflection: At $x = -1$ and $x = 1$, $g'' = 0$ and concavity changes. 
- Concave up on $(-1, 1)$, concave down on $(-\infty, -1)$, so change at $x = -1$ ✓
- Concave down on $(1, \infty)$, concave up on $(-1, 1)$, so change at $x = 1$ ✓

Points of inflection at $(-1, \ln 2)$ and $(1, \ln 2)$.

**(e)**
Key features:
- Even function (symmetric about $y$-axis)
- Local minimum at $(0, 0)$
- Points of inflection at $(-1, \ln 2)$ and $(1, \ln 2)$
- Concave up on $(-1, 1)$
- Concave down on $(-\infty, -1) \cup (1, \infty)$
- Horizontal asymptote: as $|x| \to \infty$, $g(x) \to \infty$ (no horizontal asymptote)

## Explanation
This problem requires comprehensive analysis of a transcendental function using all derivative tests.
