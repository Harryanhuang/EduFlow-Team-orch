---
id: T14-Item12
difficulty: S
calculator: no-calc
type: mcq
---
Which of the following limits CANNOT be evaluated using L'Hôpital's Rule?

## Options
A) $\displaystyle \lim_{x \to 0} \frac{\sin x}{x}$
B) $\displaystyle \lim_{x \to 0} \frac{e^x - 1}{x^2}$
C) $\displaystyle \lim_{x \to 0} \frac{\cos x - 1}{x}$
D) $\displaystyle \lim_{x \to 0} \frac{e^x}{x}$

## Answer
D) $\displaystyle \lim_{x \to 0} \frac{e^x}{x}$

## Explanation
L'Hôpital's Rule applies only to limits of the indeterminate form $0/0$ or $\infty/\infty$. For option D, as $x \to 0$ the numerator $e^x \to 1$ while the denominator $x \to 0$, giving the form $1/0$. This is not indeterminate (the limit diverges), so L'Hôpital's Rule does not apply. The other three are all $0/0$: A is the standard sine limit ($\sin 0 = 0$ over $0$), B has numerator $e^x - 1 \to 0$ over $x^2 \to 0$, and C has $\cos 0 - 1 = 0$ over $0$.
