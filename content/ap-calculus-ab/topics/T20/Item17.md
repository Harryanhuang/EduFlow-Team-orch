---
id: T20-Item17
difficulty: C
calculator: calc
type: mcq
---
A function $f$ is continuous on $[0, 10]$ and its derivative is continuous. The function $A$ is defined by $A(x) = \int_0^x f(t) \, dt$. The graph of $y = f'(x)$ is shown below.

(Graph: $f'(x)$ is a line from $(0,4)$ to $(5, -1)$, then a line from $(5, -1)$ to $(10, 4)$.)

If $A(5) = 12$ and $A(10) = 25$, what is the average value of $f$ on $[0, 10]$?

A) 2.5
B) 3.7
C) 3.9
D) 5

## Answer
A

## Explanation
We need $\frac{1}{10}\int_0^{10} f(x) \, dx = \frac{1}{10}A(10) = \frac{25}{10} = 2.5$

Since $A(x) = \int_0^x f(t) \, dt$, by FTC we have $\int_0^{10} f(t) \, dt = A(10) = 25$.

Average value $= \frac{1}{10}A(10) = 2.5$.

The answer is A.

Note: We don't need to use the graph of $f'$ or $A(5)$ to find this particular answer. The FTC directly gives us $\int_0^{10} f = A(10)$.
