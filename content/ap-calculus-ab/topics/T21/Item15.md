---
id: T21-Item15
difficulty: C
calculator: no-calc
type: frq
---
**Part A:** Evaluate \(\displaystyle \int e^x \sin(x)\,dx\). Show all work using integration by parts twice.

**Part B:** Find \(\displaystyle \int_0^1 x^2 e^{-x}\,dx\).

---

## Answer

**Part A:**

Let \(I = \int e^x \sin(x)\,dx\)

First integration by parts: \(u = \sin(x)\), \(dv = e^x dx\)
Then \(du = \cos(x)dx\), \(v = e^x\)

\[
I = e^x \sin(x) - \int e^x \cos(x)\,dx
\]

Second integration by parts: \(u = \cos(x)\), \(dv = e^x dx\)
Then \(du = -\sin(x)dx\), \(v = e^x\)

\[
\int e^x \cos(x)\,dx = e^x \cos(x) + \int e^x \sin(x)\,dx = e^x \cos(x) + I
\]

Substitute back:
\[
I = e^x \sin(x) - [e^x \cos(x) + I] = e^x \sin(x) - e^x \cos(x) - I
\]

\[
2I = e^x(\sin(x) - \cos(x))
\]

\[
I = \frac{e^x(\sin(x) - \cos(x))}{2} + C
\]

**Part B:**

Use integration by parts. Let \(u = x^2\), \(dv = e^{-x}dx\)
Then \(du = 2x\,dx\), \(v = -e^{-x}\)

\[
\int x^2 e^{-x}\,dx = -x^2 e^{-x} + \int 2x e^{-x}\,dx
\]

For \(\int 2x e^{-x}\,dx\): let \(u = 2x\), \(dv = e^{-x}dx\)
Then \(du = 2dx\), \(v = -e^{-x}\)

\[
\int 2x e^{-x}\,dx = -2x e^{-x} + \int 2e^{-x}\,dx = -2x e^{-x} - 2e^{-x}
\]

So:
\[
\int x^2 e^{-x}\,dx = -x^2 e^{-x} - 2x e^{-x} - 2e^{-x} = -e^{-x}(x^2 + 2x + 2)
\]

Evaluate from 0 to 1:

\[
\left[-e^{-1}(1 + 2 + 2)\right] - \left[-e^{0}(0 + 0 + 2)\right] = \left[-\frac{5}{e}\right] - [-2] = 2 - \frac{5}{e}
\]
