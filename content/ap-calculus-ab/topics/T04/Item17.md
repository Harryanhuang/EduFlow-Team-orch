---
id: T04-Item17
difficulty: C
calculator: no-calc
type: frq
---
Let $f(x) = \dfrac{x}{\sqrt{x^2 + 1}}$.

(a) Evaluate $\displaystyle \lim_{x \to \infty} f(x)$ and $\displaystyle \lim_{x \to -\infty} f(x)$.
(b) Does $f$ have any vertical asymptotes? Justify.
(c) Sketch a description of the graph of $f$ based on parts (a) and (b): state the horizontal asymptotes, whether $f$ is increasing or decreasing, and the range of $f$.

## Answer
(a) For $x > 0$: $\sqrt{x^2 + 1} = x\sqrt{1 + 1/x^2}$, so
$$\lim_{x \to \infty} \frac{x}{x\sqrt{1 + 1/x^2}} = \lim_{x \to \infty} \frac{1}{\sqrt{1 + 1/x^2}} = \frac{1}{\sqrt{1 + 0}} = 1.$$

For $x < 0$: $\sqrt{x^2 + 1} = |x|\sqrt{1 + 1/x^2} = -x\sqrt{1 + 1/x^2}$ (since $x < 0$, $|x| = -x$), so
$$\lim_{x \to -\infty} \frac{x}{-x\sqrt{1 + 1/x^2}} = \lim_{x \to -\infty} \frac{-1}{\sqrt{1 + 1/x^2}} = \frac{-1}{1} = -1.$$

Horizontal asymptotes: $y = 1$ as $x \to \infty$, $y = -1$ as $x \to -\infty$.

(b) No vertical asymptotes. The denominator $\sqrt{x^2 + 1} \geq 1 > 0$ for all real $x$, so it is never zero. The function is continuous everywhere.

(c) $f'(x) = \dfrac{\sqrt{x^2+1} - x \cdot \frac{x}{\sqrt{x^2+1}}}{x^2 + 1} = \dfrac{x^2 + 1 - x^2}{(x^2 + 1)^{3/2}} = \dfrac{1}{(x^2+1)^{3/2}} > 0$ for all $x$. So $f$ is strictly increasing on $\mathbb{R}$. The range is $(-1, 1)$. The graph rises from $y = -1$ (left) toward $y = 1$ (right), passing through the origin $(0, 0)$.
