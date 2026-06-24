---
id: T04-Item18
difficulty: C
calculator: no-calc
type: frq
---
Consider the function $f(x) = \ln(x) - \dfrac{1}{x - 2}$ on the domain $(0, 2) \cup (2, \infty)$.

(a) Evaluate $\displaystyle \lim_{x \to 2^{+}} f(x)$ and $\displaystyle \lim_{x \to 2^{-}} f(x)$.
(b) Evaluate $\displaystyle \lim_{x \to \infty} f(x)$ and $\displaystyle \lim_{x \to 0^{+}} f(x)$.
(c) Use the Intermediate Value Theorem to prove that the equation $\ln(x) = \dfrac{1}{x - 2}$ has at least one solution in $(0, 2)$ and at least one solution in $(2, \infty)$.

## Answer
(a) As $x \to 2^{+}$: $\ln(x) \to \ln(2)$ and $\frac{1}{x-2} \to +\infty$, so $f(x) \to \ln(2) - \infty = -\infty$.
As $x \to 2^{-}$: $\ln(x) \to \ln(2)$ and $\frac{1}{x-2} \to -\infty$, so $f(x) \to \ln(2) - (-\infty) = +\infty$.

(b) As $x \to \infty$: $\ln(x) \to \infty$ and $\frac{1}{x-2} \to 0$, so $f(x) \to \infty$.
As $x \to 0^{+}$: $\ln(x) \to -\infty$ and $\frac{1}{x-2} \to -\frac{1}{2}$, so $f(x) \to -\infty$.

(c) On $(0, 2)$: $f$ is continuous on $(0, 2)$. Pick $x = 1$: $f(1) = \ln(1) - \frac{1}{1-2} = 0 + 1 = 1 > 0$. From (a), $\lim_{x \to 2^{-}} f(x) = +\infty > 0$. From (b), $\lim_{x \to 0^{+}} f(x) = -\infty < 0$. By IVT on $(0, 1)$, since $f$ is continuous and goes from $-\infty$ to $f(1) = 1 > 0$, there exists $c_1 \in (0, 1)$ such that $f(c_1) = 0$.

On $(2, \infty)$: $f$ is continuous on $(2, \infty)$. From (a), $\lim_{x \to 2^{+}} f(x) = -\infty < 0$. From (b), $\lim_{x \to \infty} f(x) = \infty > 0$. Pick $x = 3$: $f(3) = \ln(3) - 1 \approx 1.099 - 1 > 0$. By IVT on $(2, 3)$, since $f$ is continuous and goes from $-\infty$ to $f(3) > 0$, there exists $c_2 \in (2, 3)$ such that $f(c_2) = 0$.

Thus the equation $\ln(x) = \frac{1}{x-2}$ has at least one solution in each of $(0, 2)$ and $(2, \infty)$.
