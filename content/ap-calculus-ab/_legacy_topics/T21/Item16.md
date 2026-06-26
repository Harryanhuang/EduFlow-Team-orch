---
id: T21-Item16
difficulty: C
calculator: calc
type: frq
---
The region \(R\) is bounded by the curves \(y = e^x\), \(y = e^{-x}\), and \(x = \ln(3)\).

**Part A:** Find the area of region \(R\).

**Part B:** Find the volume of the solid generated when region \(R\) is rotated about the x-axis.

---

## Answer

**Part A:**

The curves \(y = e^x\) and \(y = e^{-x}\) intersect when \(e^x = e^{-x}\), so \(2x = 0\) and \(x = 0\).

The vertical boundary is at \(x = \ln(3)\).

Area:
\[
\text{Area} = \int_0^{\ln(3)} (e^x - e^{-x})\,dx = \left[e^x + e^{-x}\right]_0^{\ln(3)}
\]

\[
= (e^{\ln(3)} + e^{-\ln(3)}) - (e^0 + e^0) = (3 + \frac{1}{3}) - (1 + 1) = \frac{10}{3} - 2 = \frac{4}{3}
\]

**Part B:**

Using the washer method (vertical slices, rotating about x-axis):

The outer radius is \(e^x\) and the inner radius is \(e^{-x}\).

\[
V = \pi\int_0^{\ln(3)} \left[(e^x)^2 - (e^{-x})^2\right]\,dx = \pi\int_0^{\ln(3)} (e^{2x} - e^{-2x})\,dx
\]

\[
= \pi\left[\frac{e^{2x}}{2} + \frac{e^{-2x}}{2}\right]_0^{\ln(3)} = \frac{\pi}{2}\left[(e^{2\ln(3)} + e^{-2\ln(3)}) - (e^0 + e^0)\right]
\]

\[
= \frac{\pi}{2}\left[(9 + \frac{1}{9}) - 2\right] = \frac{\pi}{2}\cdot\frac{64}{9} = \frac{32\pi}{9}
\]
