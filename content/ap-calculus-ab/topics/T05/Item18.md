---
id: T05-Item18
difficulty: C
calculator: no-calc
type: frq
---
Let
$$g(x) = \begin{cases} \dfrac{\sin x}{x} & \text{if } x \neq 0 \\ 1 & \text{if } x = 0 \end{cases}$$

(a) Show that $g$ is continuous at $x = 0$.

(b) Use the limit definition of the derivative to determine whether $g$ is differentiable at $x = 0$. If it is, find $g'(0)$.

(c) Explain why the result in part (b) makes sense graphically.

## Answer
(a) We need to show $\lim_{x \to 0} g(x) = g(0) = 1$. Since $\displaystyle\lim_{x \to 0} \frac{\sin x}{x} = 1$ (a standard limit), and $g(0) = 1$, $g$ is continuous at $x = 0$.

(b) Apply the limit definition:
$$g'(0) = \lim_{h \to 0} \frac{g(0 + h) - g(0)}{h} = \lim_{h \to 0} \frac{\frac{\sin h}{h} - 1}{h}$$
$$= \lim_{h \to 0} \frac{\sin h - h}{h^2}$$

Using the Taylor expansion $\sin h = h - \dfrac{h^3}{6} + O(h^5)$:
$$\frac{\sin h - h}{h^2} = \frac{h - \frac{h^3}{6} + O(h^5) - h}{h^2} = \frac{-\frac{h^3}{6} + O(h^5)}{h^2} = -\frac{h}{6} + O(h^3)$$

So $\displaystyle\lim_{h \to 0} \frac{\sin h - h}{h^2} = 0$. Therefore $g'(0) = 0$.

Alternatively, applying L'Hopital's Rule twice:
$$\lim_{h \to 0} \frac{\sin h - h}{h^2} = \lim_{h \to 0} \frac{\cos h - 1}{2h} = \lim_{h \to 0} \frac{-\sin h}{2} = 0$$

(c) The graph of $g(x) = \frac{\sin x}{x}$ has a removable discontinuity at $x = 0$ that is "filled in" by defining $g(0) = 1$. The filled-in point is the peak of a smooth "hump," so the tangent line is horizontal there, consistent with $g'(0) = 0$.

## Explanation
This problem combines continuity, the limit definition of the derivative, and analysis of a function with a removable discontinuity. Students must handle a non-polynomial limit carefully, either through series expansion or L'Hopital's Rule. The connection between the algebraic result and the graphical behavior reinforces conceptual understanding.
