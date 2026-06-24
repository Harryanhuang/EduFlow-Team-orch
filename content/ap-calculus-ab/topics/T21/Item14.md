---
id: T21-Item14
difficulty: C
calculator: no-calc
type: frq
---
**Part A:** Evaluate \(\displaystyle \int \frac{4x}{(x-2)^2}\,dx\). Show all work.

**Part B:** Write the antiderivative \(F(x)\) of \(f(x) = \sin(x)\cos(x)\) that satisfies \(F(0) = 2\).

---

## Answer

**Part A:**

Use partial fractions: Let \(\frac{4x}{(x-2)^2} = \frac{A}{x-2} + \frac{B}{(x-2)^2}\)

So \(4x = A(x-2) + B = Ax - 2A + B\)

Equating coefficients: \(A = 4\) (coefficient of x), and \(-2A + B = 0\) so \(B = 8\).

Thus: \(\int \frac{4x}{(x-2)^2}\,dx = \int \left(\frac{4}{x-2} + \frac{8}{(x-2)^2}\right)dx\)

\[
= 4\ln|x-2| - \frac{8}{x-2} + C
\]

(For \(\int \frac{8}{(x-2)^2}dx\): let \(u = x-2\), then \(\int 8u^{-2}du = 8(-1)u^{-1} = -\frac{8}{u}\))

**Part B:**

\(F(x) = \int \sin(x)\cos(x)\,dx\)

Use substitution: Let \(u = \sin(x)\), \(du = \cos(x)\,dx\)

\[
F(x) = \int u\,du = \frac{u^2}{2} + C = \frac{\sin^2(x)}{2} + C
\]

Using \(F(0) = 2\): \(\frac{\sin^2(0)}{2} + C = 0 + C = 2\), so \(C = 2\).

Thus: \(F(x) = \frac{\sin^2(x)}{2} + 2\)
