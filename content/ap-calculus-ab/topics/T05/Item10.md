---
id: T05-Item10
difficulty: S
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{1}{x}$.

(a) Use the limit definition of the derivative to find $f'(x)$.

(b) Find the equation of the tangent line to the graph of $f$ at $x = 2$.

## Answer
(a) 
$$f'(x) = \lim_{h \to 0} \frac{f(x + h) - f(x)}{h} = \lim_{h \to 0} \frac{\frac{1}{x + h} - \frac{1}{x}}{h}$$
$$= \lim_{h \to 0} \frac{x - (x + h)}{hx(x + h)} = \lim_{h \to 0} \frac{-h}{hx(x + h)}$$
$$= \lim_{h \to 0} \frac{-1}{x(x + h)} = \frac{-1}{x^2}$$

(b) $f'(2) = -\dfrac{1}{4}$ and $f(2) = \dfrac{1}{2}$. The tangent line is:
$$y - \frac{1}{2} = -\frac{1}{4}(x - 2) \implies y = -\frac{1}{4}x + 1$$

## Explanation
Part (a) requires combining the fractions in the numerator, simplifying the complex fraction, canceling $h$, and evaluating the limit. Part (b) evaluates the derivative and function at $x = 2$, then uses point-slope form to find the tangent line.
