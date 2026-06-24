---
id: T14-Item15
difficulty: S
calculator: calc
type: frq
---
Evaluate $\displaystyle \lim_{x \to \infty} \frac{\ln(x + 1)}{\sqrt{x}}$.

## Answer
0

## Explanation
As $x \to \infty$, $\ln(x+1) \to \infty$ and $\sqrt{x} \to \infty$, giving ∞/∞. Apply L'Hôpital's Rule:
$\displaystyle \lim_{x \to \infty} \frac{\ln(x + 1)}{\sqrt{x}} = \lim_{x \to \infty} \frac{1/(x+1)}{1/(2\sqrt{x})} = \lim_{x \to \infty} \frac{2\sqrt{x}}{x+1}$.
This is still ∞/∞. Apply L'Hôpital's Rule again:
$\displaystyle \lim_{x \to \infty} \frac{2 \cdot \frac{1}{2\sqrt{x}}}{1} = \lim_{x \to \infty} \frac{1}{\sqrt{x}} = 0$.
