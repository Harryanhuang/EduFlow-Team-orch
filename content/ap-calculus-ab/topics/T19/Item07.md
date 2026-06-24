---
id: T19-Item07
difficulty: F
calculator: no-calc
type: mcq
---

The definite integral $\displaystyle\int_0^4 f(x)\,dx$ can be expressed as which of the following limits of Riemann sums?

A) $\displaystyle\lim_{n\to\infty}\sum_{i=1}^n \frac{4}{n}f\!\left(\frac{4i}{n}\right)$

B) $\displaystyle\lim_{n\to\infty}\sum_{i=1}^n \frac{4}{n}f\!\left(\frac{4(i-1)}{n}\right)$

C) $\displaystyle\lim_{n\to\infty}\sum_{i=1}^n \frac{4i}{n}\,f\!\left(\frac{4}{n}\right)$

D) $\displaystyle\lim_{n\to\infty}\sum_{i=1}^n f\!\left(\frac{4i}{n}\right)$

## Answer

A

## Explanation

For a right Riemann sum on $[a,b]$ with $n$ subintervals:
- Each subinterval has width $\Delta x = \frac{b-a}{n} = \frac{4}{n}$
- The right endpoint of the $i$th subinterval is $x_i = a + i\Delta x = \frac{4i}{n}$
- The Riemann sum is $\sum_{i=1}^n f(x_i)\Delta x = \sum_{i=1}^n \frac{4}{n}\,f\!\left(\frac{4i}{n}\right)$
- Taking the limit as $n\to\infty$ gives the definite integral.

Option B represents a **left** Riemann sum (using $x_{i-1}$ endpoints).
Option C has the width $\Delta x$ applied to the wrong factor and is not a valid Riemann sum.
Option D is missing the $\Delta x$ factor entirely.

The correct answer is **A**.
