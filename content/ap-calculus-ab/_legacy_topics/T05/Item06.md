---
id: T05-Item06
difficulty: S
calculator: no-calc
type: frq
---
Let $f(x) = x^2 - 4x$.

(a) Use the limit definition of the derivative to find $f'(x)$.

(b) Find the equation of the tangent line to the graph of $f$ at $x = 3$.

## Answer
(a) 
$$f'(x) = \lim_{h \to 0} \frac{f(x + h) - f(x)}{h}$$
$$= \lim_{h \to 0} \frac{[(x + h)^2 - 4(x + h)] - [x^2 - 4x]}{h}$$
$$= \lim_{h \to 0} \frac{x^2 + 2xh + h^2 - 4x - 4h - x^2 + 4x}{h}$$
$$= \lim_{h \to 0} \frac{2xh + h^2 - 4h}{h} = \lim_{h \to 0}(2x + h - 4) = 2x - 4$$

(b) $f'(3) = 2(3) - 4 = 2$. Also $f(3) = 9 - 12 = -3$. The tangent line is:
$$y - (-3) = 2(x - 3) \implies y = 2x - 9$$

## Explanation
Part (a) requires expanding $(x+h)^2$, distributing the $-4$, canceling terms, factoring out $h$, and taking the limit. Part (b) uses the derivative value as the slope and the point $(3, f(3)) = (3, -3)$ to write the tangent line equation in point-slope form, then simplifying to slope-intercept form.
