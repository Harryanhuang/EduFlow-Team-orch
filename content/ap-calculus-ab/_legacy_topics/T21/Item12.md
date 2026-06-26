---
id: T21-Item12
difficulty: S
calculator: calc
type: mcq
---
The region bounded by the curves \(y = x^2\) and \(y = 2x\) is rotated about the x-axis. What is the volume of the solid generated?

## Options
A) \(\frac{16\pi}{15}\)
B) \(\frac{8\pi}{3}\)
C) \(\frac{4\pi}{3}\)
D) \(\frac{16\pi}{3}\)

## Answer
B

## Explanation
First, find where the curves intersect: \(x^2 = 2x\) gives \(x(x-2) = 0\), so \(x = 0\) and \(x = 2\).

For \(0 \leq x \leq 2\), \(2x \geq x^2\), so the outer radius is \(2x\) and the inner radius is \(x^2\).

Using the washer method (horizontal slices, rotating about x-axis):

\(y = x^2\) gives \(x = \sqrt{y}\), and \(y = 2x\) gives \(x = y/2\).
When \(x = 0\), \(y = 0\); when \(x = 2\), \(y = 4\).

Outer radius: \(R = \sqrt{y}\), Inner radius: \(r = y/2\).

\[
V = \pi\int_0^4 \left[(\sqrt{y})^2 - \left(\frac{y}{2}\right)^2\right]\,dy = \pi\int_0^4 \left(y - \frac{y^2}{4}\right)dy
\]

\[
= \pi\left[\frac{y^2}{2} - \frac{y^3}{12}\right]_0^4 = \pi\left(8 - \frac{64}{12}\right) = \pi\left(8 - \frac{16}{3}\right) = \frac{8\pi}{3}
\]
