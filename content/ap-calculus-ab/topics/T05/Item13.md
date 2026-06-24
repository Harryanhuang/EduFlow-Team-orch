---
id: T05-Item13
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \sqrt{x}$.

(a) Use the limit definition of the derivative to find $f'(x)$ for $x > 0$.

(b) Show that $f$ is not differentiable at $x = 0$ by analyzing the limit definition.

(c) Is $f$ continuous at $x = 0$? What does this tell you about the relationship between continuity and differentiability?

## Answer
(a) 
$$f'(x) = \lim_{h \to 0} \frac{\sqrt{x + h} - \sqrt{x}}{h}$$
Multiply by the conjugate:
$$= \lim_{h \to 0} \frac{\sqrt{x + h} - \sqrt{x}}{h} \cdot \frac{\sqrt{x + h} + \sqrt{x}}{\sqrt{x + h} + \sqrt{x}}$$
$$= \lim_{h \to 0} \frac{(x + h) - x}{h(\sqrt{x + h} + \sqrt{x})} = \lim_{h \to 0} \frac{h}{h(\sqrt{x + h} + \sqrt{x})}$$
$$= \lim_{h \to 0} \frac{1}{\sqrt{x + h} + \sqrt{x}} = \frac{1}{2\sqrt{x}}$$

(b) At $x = 0$:
$$\lim_{h \to 0^+} \frac{\sqrt{0 + h} - \sqrt{0}}{h} = \lim_{h \to 0^+} \frac{\sqrt{h}}{h} = \lim_{h \to 0^+} \frac{1}{\sqrt{h}} = +\infty$$
The limit does not exist (it diverges to infinity), so $f'(0)$ does not exist. The graph has a vertical tangent at $x = 0$.

(c) Yes, $f$ is continuous at $x = 0$ because $\lim_{x \to 0^+} \sqrt{x} = 0 = f(0)$. This demonstrates that a function can be continuous at a point without being differentiable there. Continuity is necessary but not sufficient for differentiability.

## Explanation
Part (a) requires the conjugate multiplication technique for rationalizing the numerator. Part (b) shows the limit diverges, which corresponds to a vertical tangent line. Part (c) reinforces the key concept that continuity does not imply differentiability — a core idea in CED 2.2.
