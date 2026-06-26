---
id: T02-Item03
difficulty: F
calculator: no-calc
type: frq
---
Evaluate the limit:

$\displaystyle \lim_{x \to 0} \frac{\sqrt{x + 4} - 2}{x}$

## Answer
$\dfrac{1}{4}$

## Explanation
Multiply numerator and denominator by the conjugate $\sqrt{x + 4} + 2$:

$$\frac{\sqrt{x + 4} - 2}{x} \cdot \frac{\sqrt{x + 4} + 2}{\sqrt{x + 4} + 2} = \frac{(x + 4) - 4}{x(\sqrt{x + 4} + 2)} = \frac{x}{x(\sqrt{x + 4} + 2)}$$

For $x \neq 0$:
$$= \frac{1}{\sqrt{x + 4} + 2}$$

$$\lim_{x \to 0} \frac{1}{\sqrt{x + 4} + 2} = \frac{1}{\sqrt{4} + 2} = \frac{1}{4}$$
