---
id: T15-Item08
difficulty: S
calculator: no-calc
type: frq
---
The graph of $f'(x)$, the derivative of a continuous function $f$, is shown below. The domain of $f$ is $[-4, 6]$.

```
         f'(x)
          ^
      4 - |        /\
          |       /  \
      2 - |  /\  /    \
          | /  \/      \
  --------+-------------> x
     -4 - |  \  /\      \     6
          |   \/  \      \
     -2 - |        \      \
          |         \______\
```

The graph consists of line segments connecting the points $(-4, 0)$, $(-2, 2)$, $(0, 0)$, $(2, 4)$, $(4, 0)$, and $(6, -2)$.

(a) On what intervals is $f$ increasing?
(b) Find all values of $x$ in $(-4, 6)$ where $f$ has a local maximum. Justify your answer.
(c) If $f(0) = 5$, find the absolute minimum value of $f$ on $[-4, 6]$.

## Answer
(a) $f$ is increasing where $f'(x) > 0$: on $(-4, 0)$ and $(0, 4)$. So $f$ is increasing on $(-4, 4)$.
(b) $f$ has a local maximum at $x = 4$, since $f'$ changes from positive to negative there. At $x = 0$, $f' = 0$ but does not change sign (positive on both sides), so no extremum.
(c) Compute $f$ at critical points and endpoints using areas under $f'$:
$f(-4) = f(0) - \int_{-4}^{0} f'(t)\,dt = 5 - [\text{area}] = 5 - \frac{1}{2}(4)(2) = 5 - 4 = 1$
$f(4) = f(0) + \int_{0}^{4} f'(t)\,dt = 5 + \frac{1}{2}(4)(4) = 5 + 8 = 13$
$f(6) = f(4) + \int_{4}^{6} f'(t)\,dt = 13 + \frac{1}{2}(2)(-2) = 13 - 2 = 11$
Absolute minimum is $f(-4) = 1$.

## Explanation
Since $f$ is continuous and differentiable (given $f'$ exists), we use the relationship between $f$ and $f'$. $f$ increases when $f' > 0$ and decreases when $f' < 0$. Local extrema occur where $f'$ changes sign. Absolute extrema on a closed interval are found by evaluating $f$ at critical points and endpoints. The net change in $f$ equals the signed area under $f'$.
