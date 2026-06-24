---
id: T02-Item15
difficulty: C
calculator: no-calc
type: frq
---
Evaluate the limit:

$\displaystyle \lim_{x \to 0} \frac{\sqrt{x + 9} - 3}{\sqrt{x + 4} - 2}$

## Answer
$\dfrac{2}{3}$

## Explanation
Both numerator and denominator give $0$ at $x = 0$. Rationalize by multiplying numerator and denominator by both conjugates:

$$\frac{\sqrt{x + 9} - 3}{\sqrt{x + 4} - 2} \cdot \frac{\sqrt{x + 9} + 3}{\sqrt{x + 9} + 3} \cdot \frac{\sqrt{x + 4} + 2}{\sqrt{x + 4} + 2}$$

$$= \frac{[(x + 9) - 9](\sqrt{x + 4} + 2)}{[(x + 4) - 4](\sqrt{x + 9} + 3)} = \frac{x(\sqrt{x + 4} + 2)}{x(\sqrt{x + 9} + 3)}$$

For $x \neq 0$:
$$= \frac{\sqrt{x + 4} + 2}{\sqrt{x + 9} + 3}$$

$$\lim_{x \to 0} \frac{\sqrt{x + 4} + 2}{\sqrt{x + 9} + 3} = \frac{2 + 2}{3 + 3} = \frac{4}{6} = \frac{2}{3}$$
