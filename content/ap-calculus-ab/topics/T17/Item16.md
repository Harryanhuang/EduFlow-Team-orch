---
id: T17-Item16
difficulty: C
calculator: calc
type: frq
---
The function $f$ is continuous on $[-3, 3]$ and differentiable on $(-3, 3)$. Selected values are given below.

| $x$ | $-3$ | $-2$ | $-1$ | $0$ | $1$ | $2$ | $3$ |
|-----|------|------|------|-----|-----|-----|-----|
| $f(x)$ | $4$ | $2$ | $0$ | $-1$ | $0$ | $2$ | $4$ |
| $f'(x)$ | $2$ | $1$ | $0$ | $-1$ | $0$ | $1$ | $2$ |

**(a)** Using the data, estimate where $f$ is concave up and where $f$ is concave down.

**(b)** Estimate the $x$-coordinates of any points of inflection of $f$.

**(c)** Using the Second Derivative Test, classify any critical points of $f$ where possible.

**(d)** Suppose $f''(x) = 0$ has solutions at $x = -1$ and $x = 1$. Use this information along with parts (a)-(c) to sketch a possible graph of $f$.

## Answer
**(a)**
Using the sign of $f'$ as a proxy for concavity changes:
- From $x = -3$ to $x = -1$: $f'$ decreases from $2$ to $0$ → $f'' < 0$ → concave down
- From $x = -1$ to $x = 1$: $f'$ decreases from $0$ to $-1$ through... wait, let me check monotonicity.

Actually, $f'$ itself is decreasing on $(-3, 1)$ and increasing on $(1, 3)$.
So $f'' < 0$ on $(-3, 1)$ and $f'' > 0$ on $(1, 3)$.

Concave down on $(-3, 1)$, concave up on $(1, 3)$.

**(b)**
Point of inflection where concavity changes: $x = 1$

Also, at $x = -1$, $f'(x) = 0$ but the concavity doesn't necessarily change there.

**(c)**
Critical points occur where $f'(x) = 0$: $x = -1$ and $x = 1$.

At $x = -1$: $f''(-1) < 0$ (since concave down on $(-3, 1)$) → local maximum
At $x = 1$: $f''(1) > 0$ (since concave up on $(1, 3)$) → local minimum

**(d)**
Graph features:
- Local maximum at $x = -1$, $f(-1) = 0$
- Local minimum at $x = 1$, $f(1) = 0$
- Concave down from $x = -3$ to $x = 1$
- Concave up from $x = 1$ to $x = 3$
- Passes through $(-3, 4)$, $(0, -1)$, $(2, 2)$, $(3, 4)$

## Explanation
This problem uses a table of values to reconstruct information about derivatives and their behavior.
