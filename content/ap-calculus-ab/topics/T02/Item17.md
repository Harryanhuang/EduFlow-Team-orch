---
id: T02-Item17
difficulty: C
calculator: no-calc
type: frq
---
Use the Squeeze Theorem to evaluate:

$\displaystyle \lim_{x \to 0} x^4 \cos\left(\frac{2}{x}\right)$

Justify your choice of bounding functions.

## Answer
$0$

## Explanation
Since $-1 \leq \cos\left(\dfrac{2}{x}\right) \leq 1$ for all $x \neq 0$:

Multiply all parts by $x^4$ (note: $x^4 \geq 0$ for all real $x$, so inequality direction is preserved):

$$-x^4 \leq x^4 \cos\left(\frac{2}{x}\right) \leq x^4$$

Evaluate the limits of the bounding functions:
$$\lim_{x \to 0} (-x^4) = 0 \quad \text{and} \quad \lim_{x \to 0} x^4 = 0$$

By the Squeeze Theorem:
$$\lim_{x \to 0} x^4 \cos\left(\frac{2}{x}\right) = 0$$

The bounding functions $g(x) = -x^4$ and $h(x) = x^4$ are chosen because they are the tightest polynomial bounds that follow directly from the range of cosine.
