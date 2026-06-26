---
id: T20-Item08
difficulty: S
calculator: calc
type: mcq
---
The function $f$ is continuous and has the values shown in the table:

| $x$ | 0 | 2 | 4 | 6 |
|-----|-----|-----|-----|-----|
| $f(x)$ | 1 | 3 | 5 | 4 |

Using a left Riemann sum with three subintervals of equal width, the average value of $f$ on $[0, 6]$ is approximately

A) 2.5
B) 3.0
C) 3.5
D) 4.0

## Answer
C

## Explanation
The average value formula is $\frac{1}{b-a}\int_a^b f(x) \, dx$.

With three subintervals of width 2: $[0,2]$, $[2,4]$, $[4,6]$.

Using the trapezoid rule for approximation:
$\int_0^6 f(x) \, dx \approx 2 \cdot \frac{f(0)+f(2)}{2} + 2 \cdot \frac{f(2)+f(4)}{2} + 2 \cdot \frac{f(4)+f(6)}{2}$
$= (1+3) + (3+5) + (5+4) = 4 + 8 + 9 = 21$

Average value $\approx \frac{1}{6} \cdot 21 = 3.5$
