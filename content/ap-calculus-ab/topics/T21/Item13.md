---
id: T21-Item13
difficulty: C
calculator: no-calc
type: frq
---
**Part A:** Evaluate \(\displaystyle \int_1^4 \frac{x^2 - 3x + 1}{x}\,dx\). Show all work.

**Part B:** Find the area of the region enclosed by the curves \(y = x^2 - 4x + 3\) and \(y = x - 1\). Set up but do not evaluate the integral that represents this area.

---

## Answer

**Part A:**

\[
\int_1^4 \frac{x^2 - 3x + 1}{x}\,dx = \int_1^4 \left(x - 3 + \frac{1}{x}\right)dx = \left[\frac{x^2}{2} - 3x + \ln|x|\right]_1^4
\]

\[
= \left(\frac{16}{2} - 12 + \ln 4\right) - \left(\frac{1}{2} - 3 + \ln 1\right) = (8 - 12 + \ln 4) - (0.5 - 3 + 0)
\]

\[
= (-4 + \ln 4) - (-2.5) = -4 + \ln 4 + 2.5 = \ln 4 - \frac{3}{2}
\]

**Part B:**

Find intersections: \(x^2 - 4x + 3 = x - 1\) gives \(x^2 - 5x + 4 = 0\), so \((x-1)(x-4) = 0\), giving \(x = 1\) and \(x = 4\).

For \(1 < x < 4\), the line \(y = x - 1\) is above the parabola \(y = x^2 - 4x + 3\).

\[
\text{Area} = \int_1^4 \left[(x - 1) - (x^2 - 4x + 3)\right]\,dx = \int_1^4 (-x^2 + 5x - 4)\,dx
\]
