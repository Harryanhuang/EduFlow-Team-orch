---
id: T19-Item13
difficulty: F
calculator: no-calc
type: mcq
---

Let $f$ be a continuous function on $[2, 9]$. The area under $f$ from $x = 2$ to $x = 9$ can be expressed as which of the following limits of Riemann sums?

## Options
A) $\displaystyle\lim_{n \to \infty} \sum_{i=1}^{n} f(2 + i\Delta x)\,\Delta x$, where $\Delta x = \dfrac{7}{n}$

B) $\displaystyle\lim_{n \to \infty} \sum_{i=1}^{n} f(2 + i\Delta x)\,\Delta x$, where $\Delta x = \dfrac{9}{n}$

C) $\displaystyle\lim_{n \to \infty} \sum_{i=1}^{n} f(2 + (i-1)\Delta x)\,\Delta x$, where $\Delta x = \dfrac{7}{n}$

D) $\displaystyle\lim_{n \to \infty} \sum_{i=1}^{n} f(2 + (i-1)\Delta x)\,\Delta x$, where $\Delta x = \dfrac{9}{n}$

## Answer
A

## Explanation
The definite integral $\int_2^9 f(x)\,dx$ is defined as the limit of Riemann sums. With $n$ subintervals of equal width over $[2, 9]$:

$$\Delta x = \frac{b-a}{n} = \frac{9-2}{n} = \frac{7}{n}$$

For a **right** Riemann sum, the $i$-th sample point is:
$$x_i^* = a + i\Delta x = 2 + i\Delta x$$

So the sum is $\sum_{i=1}^{n} f(2 + i\Delta x)\,\Delta x$ with $\Delta x = \frac{7}{n}$.

Option A is correct. Option B is wrong because $\Delta x$ must be $\frac{7}{n}$, not $\frac{9}{n}$. Option C uses left-endpoint sampling ($i-1$), which would correspond to a left Riemann sum. Option D has both the wrong sample points and wrong $\Delta x$.
