---
id: T18-Item17
difficulty: C
calculator: calc
type: frq
---
A line through $(3, 4)$ intersects the positive x-axis at $A(a, 0)$ and the positive y-axis at $B(0, b)$.

(a) Express the area of triangle $AOB$ (where $O$ is the origin) as a function of $a$.
(b) Find the values of $a$ and $b$ that minimize the area of triangle $AOB$.
(c) What is the minimum area?

## Answer
(a) $A(a) = \frac{2a^2}{a-3}$ for $a > 3$

(b) $a = 6$, $b = 8$

(c) $A_{min} = 24$

## Explanation
(a) Line through $(3,4)$ with intercepts $(a,0)$ and $(0,b)$: $\frac{x}{a} + \frac{y}{b} = 1$. Since $(3,4)$ is on the line: $\frac{3}{a} + \frac{4}{b} = 1$, so $b = \frac{4a}{a-3}$. Area of triangle with intercepts $a$ and $b$: $A = \frac{1}{2}ab = \frac{1}{2}a \cdot \frac{4a}{a-3} = \frac{2a^2}{a-3}$.

(b) $A'(a) = \frac{4a(a-3) - 2a^2 \cdot 1}{(a-3)^2} = \frac{4a^2 - 12a - 2a^2}{(a-3)^2} = \frac{2a^2 - 12a}{(a-3)^2} = \frac{2a(a - 6)}{(a-3)^2} = 0$.
So $a = 0$ or $a = 6$. $a > 3$, so $a = 6$. Then $b = \frac{4(6)}{6-3} = \frac{24}{3} = 8$.

(c) $A(6) = \frac{2(36)}{3} = \frac{72}{3} = 24$.
