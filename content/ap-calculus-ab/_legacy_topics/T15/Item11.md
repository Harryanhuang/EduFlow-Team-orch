---
id: T15-Item11
difficulty: S
calculator: calc
type: frq
---
Let $f(x) = e^x + x$ on the interval $[-1, 2]$.

(a) By the Mean Value Theorem, there exists $c$ in $(-1, 2)$ such that $f'(c) = (f(2) - f(-1))/(2 - (-1))$. Find all such values of $c$.
(b) What does this result tell you about the average rate of change of $f$ on $[-1, 2]$?

## Answer
(a) Average rate of change:
$f(2) = e^2 + 2 \approx 7.389 + 2 = 9.389$
$f(-1) = e^{-1} - 1 \approx 0.368 - 1 = -0.632$
$(f(2) - f(-1))/3 \approx (9.389 - (-0.632))/3 = 10.021/3 \approx 3.340$
Set $f'(c) = e^c + 1 = 3.340$: $e^c = 2.340$, $c = \ln(2.340) \approx 0.850$
This is the only solution in $(-1, 2)$ since $e^x + 1$ is strictly increasing.
(b) The average rate of change is approximately 3.34, meaning $f$ increases by approximately 3.34 units per unit of $x$ on average over $[-1, 2]$.

## Explanation
Since $f(x) = e^x + x$ is continuous and differentiable everywhere, MVT applies. The average rate of change is $(e^2 + 2 - (e^{-1} - 1))/3$. Setting $f'(c) = e^c + 1$ equal to this average gives $c = \ln((e^2 + 3 - e^{-1})/3)$. Using a calculator yields $c \approx 0.850$, which lies in $(-1, 2)$.
