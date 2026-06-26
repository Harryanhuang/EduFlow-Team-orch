---
id: T02-Item18
difficulty: C
calculator: no-calc
type: frq
---
Let $h(x) = \dfrac{\sqrt{2x + 1} - \sqrt{x + 3}}{x - 2}$.

(a) Evaluate $\displaystyle \lim_{x \to 2} h(x)$.

(b) Classify the type of discontinuity at $x = 2$ and explain how $h$ could be redefined to make it continuous there.

## Answer
(a) $\dfrac{1}{2\sqrt{5}}$

(b) Removable discontinuity (a hole). Redefine $h(2) = \dfrac{1}{2\sqrt{5}}$ to make $h$ continuous.

## Explanation
**(a)** Both numerator and denominator give $0$ at $x = 2$. Rationalize the numerator:

$$\frac{\sqrt{2x + 1} - \sqrt{x + 3}}{x - 2} \cdot \frac{\sqrt{2x + 1} + \sqrt{x + 3}}{\sqrt{2x + 1} + \sqrt{x + 3}}$$

$$= \frac{(2x + 1) - (x + 3)}{(x - 2)(\sqrt{2x + 1} + \sqrt{x + 3})} = \frac{x - 2}{(x - 2)(\sqrt{2x + 1} + \sqrt{x + 3})}$$

For $x \neq 2$:
$$= \frac{1}{\sqrt{2x + 1} + \sqrt{x + 3}}$$

$$\lim_{x \to 2} \frac{1}{\sqrt{2x + 1} + \sqrt{x + 3}} = \frac{1}{\sqrt{5} + \sqrt{5}} = \frac{1}{2\sqrt{5}}$$

**(b)** Since the limit exists but $h(2)$ is undefined (division by zero), the discontinuity is removable. Redefining $h(2) = \dfrac{1}{2\sqrt{5}}$ fills the hole.
