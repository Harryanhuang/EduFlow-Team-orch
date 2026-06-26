---
id: T14-Item18
difficulty: C
calculator: no-calc
type: frq
---
Consider the function $f(x) = \dfrac{\cos x - 1}{x^2}$.

(a) Evaluate $\displaystyle \lim_{x \to 0} f(x)$. Show your work.
(b) Find the linearization $L(x)$ of $f$ at $x = 0$.
(c) Using the result of part (b), evaluate $\displaystyle \lim_{x \to 0} \frac{f(x) - L(x)}{x^2}$.
(d) Classify each of the following limits as convergent or divergent without a calculator:
    (i) $\displaystyle \lim_{x \to 0} \frac{\sin x - x}{x^3}$
    (ii) $\displaystyle \lim_{x \to 0} \frac{e^x - 1 - x - \frac{x^2}{2} - \frac{x^3}{6}}{x^4}$

## Answer
(a) $\displaystyle \lim_{x \to 0} \frac{\cos x - 1}{x^2} = -\frac{1}{2}$
(b) $L(x) = -\frac{1}{2}$
(c) $\displaystyle \lim_{x \to 0} \frac{f(x) - L(x)}{x^2} = \frac{1}{24}$
(d) (i) Convergent, value $-\frac{1}{6}$; (ii) Convergent, value $\frac{1}{24}$

## Explanation
(a) The limit has the indeterminate form $0/0$. By L'Hôpital's Rule, $\lim_{x \to 0} \frac{-\sin x}{2x} = -\frac{1}{2} \lim_{x \to 0} \frac{\sin x}{x} = -\frac{1}{2}$.
(b) Define $f$ continuously at $0$ by $f(0) = -\frac{1}{2}$. Since the function is even, $f'(0) = 0$, so the linearization is the constant $L(x) = -\frac{1}{2}$.
(c) Using the Maclaurin series $\cos x = 1 - \frac{x^2}{2} + \frac{x^4}{24} - \cdots$, we get $f(x) = \frac{\cos x - 1}{x^2} = -\frac{1}{2} + \frac{x^2}{24} - \cdots$. Then $f(x) - L(x) = \frac{x^2}{24} - \cdots$, so $\frac{f(x) - L(x)}{x^2} \to \frac{1}{24}$.
(d) (i) Apply L'Hôpital three times: $\lim \frac{\cos x - 1}{3x^2} = \lim \frac{-\sin x}{6x} = \lim \frac{-\cos x}{6} = -\frac{1}{6}$. Convergent. (ii) From $e^x = 1 + x + \frac{x^2}{2} + \frac{x^3}{6} + \frac{x^4}{24} + \cdots$, the numerator equals $\frac{x^4}{24} + O(x^5)$, so dividing by $x^4$ gives the limit $\frac{1}{24}$. Convergent.
