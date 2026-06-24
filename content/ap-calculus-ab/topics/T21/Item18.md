---
id: T21-Item18
difficulty: C
calculator: no-calc
type: frq
---
A particle moves along the x-axis with velocity \(v(t) = \sin(t)\cos^2(t)\) for \(0 \leq t \leq \frac{\pi}{2}\). The particle is at position \(x = -1\) when \(t = 0\).

**Part A:** Find the position function \(x(t)\).

**Part B:** Find the total distance traveled by the particle from \(t = 0\) to \(t = \frac{\pi}{2}\).

---

## Answer

**Part A:**

\[
x(t) = \int v(t)\,dt + x(0) = \int \sin(t)\cos^2(t)\,dt - 1
\]

Use substitution. Let \(u = \cos(t)\), so \(du = -\sin(t)\,dt\) and \(\sin(t)\,dt = -du\).

\[
\int \sin(t)\cos^2(t)\,dt = \int -u^2\,du = -\frac{u^3}{3} = -\frac{\cos^3(t)}{3}
\]

So:
\[
x(t) = -\frac{\cos^3(t)}{3} - 1 + C
\]

Using \(x(0) = -1\): \(-\frac{\cos^3(0)}{3} - 1 + C = -\frac{1}{3} - 1 + C = -1\)

So \(C = \frac{1}{3}\).

\[
x(t) = \frac{1 - \cos^3(t)}{3} - 1
\]

**Part B:**

Total distance = \(\int_0^{\pi/2} |v(t)|\,dt\)

Since \(v(t) = \sin(t)\cos^2(t)\) is non-negative on \([0, \pi/2]\) (both \(\sin(t) \geq 0\) and \(\cos^2(t) \geq 0\)), we have \(|v(t)| = v(t)\).

\[
\text{Distance} = \int_0^{\pi/2} \sin(t)\cos^2(t)\,dt
\]

Using the same substitution: \(u = \cos(t)\), \(du = -\sin(t)\,dt\)

When \(t = 0\), \(u = 1\). When \(t = \frac{\pi}{2}\), \(u = 0\).

\[
\int_1^0 -u^2\,du = \int_0^1 u^2\,du = \left[\frac{u^3}{3}\right]_0^1 = \frac{1}{3}
\]
