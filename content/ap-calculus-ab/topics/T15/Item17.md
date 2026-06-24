---
id: T15-Item17
difficulty: C
calculator: no-calc
type: frq
---
The graph of $f'$ for a function $f$ continuous on $[-2, 5]$ is shown below. $f'$ consists of line segments: $(-2, 1) \to (0, 3) \to (2, -1) \to (5, -1)$.

```
     f'(x)
       ^
   3 --|  \        /________
       |   \      /         \
   1 --|----\____/           |___ x
       |    -2   0      2     5
      -1 --|-------------------------
```

(a) On what intervals is $f$ concave down?
(b) Find all points of inflection of $f$ on $(-2, 5)$.
(c) If $f(-2) = 3$, use the graph of $f'$ to find $f(0)$, $f(2)$, and $f(5)$.
(d) Find the absolute maximum of $f$ on $[-2, 5]$, if it exists. Justify using the EVT and MVT.

## Answer
(a) $f$ is concave down where $f'' < 0$, i.e., where $f'$ is decreasing. This occurs on $(-2, 0)$ (slope of $f'$ is positive but decreasing) and on $(2, 5)$ (where $f'$ has slope $0$ and is constant at $-1$ — actually slope $0$, so concave up on $(2, 5)$?).
Wait: $f'$ is linear on each subinterval. $f''$ is the slope of $f'$.
On $(-2, 0)$: slope of $f'$ segment = $(3-1)/(0-(-2)) = 2/2 = 1 > 0$, so $f'' > 0$, concave UP.
On $(0, 2)$: slope = $(-1-3)/(2-0) = -4/2 = -2 < 0$, so $f'' < 0$, concave DOWN.
On $(2, 5)$: slope = $(-1-(-1))/(5-2) = 0$, so $f'' = 0$, linear (no concavity).
So $f$ is concave down on $(0, 2)$.
(b) Points of inflection at $x = 0$ (concave up to concave down) and $x = 2$ (concave down to neither). The point at $x = 2$ is a point of inflection because $f''$ changes sign (from negative to zero).
(c) $f(0) = f(-2) + \int_{-2}^{0} f'(t)\,dt = 3 + \frac{1}{2}(2)(1 + 3) = 3 + 4 = 7$.
$f(2) = f(0) + \int_{0}^{2} f'(t)\,dt = 7 + \frac{1}{2}(2)(3 + (-1)) = 7 + 2 = 9$.
$f(5) = f(2) + \int_{2}^{5} f'(t)\,dt = 9 + \frac{1}{2}(3)(-1 + (-1)) = 9 + \frac{1}{2}(3)(-2) = 9 - 3 = 6$.
(d) Absolute maximum: compare $f(-2) = 3$, $f(0) = 7$, $f(2) = 9$, $f(5) = 6$. Absolute maximum is $9$ at $x = 2$.

## Explanation
The connection between $f'$ and $f$ enables reconstruction of $f$ values from area under $f'$. Concavity of $f$ is determined by the monotonicity of $f'$. Points of inflection occur where $f'$ changes monotonicity. Since $f$ is continuous on a closed interval, EVT guarantees absolute extrema exist, found by evaluating at critical points and endpoints.
