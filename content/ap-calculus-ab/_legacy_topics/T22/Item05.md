---
id: T22-Item05
difficulty: F
calculator: calc
type: frq
---
A function \(y = f(x)\) satisfies the differential equation \(\dfrac{dy}{dx} = 2x + 1\).

**(a)** Find the general solution of the differential equation.

**(b)** Find the particular solution that satisfies \(f(0) = 4\).

**(c)** Verify that the particular solution from part (b) satisfies both the differential equation and the initial condition.

## Answer
**(a)** Integrate both sides:
\[y = \int (2x + 1)\,dx = x^{2} + x + C\]

**(b)** Apply \(f(0) = 4\):
\[4 = 0 + 0 + C \implies C = 4\]
So \(f(x) = x^{2} + x + 4\).

**(c)** Differentiate: \(f'(x) = 2x + 1\), which matches the differential equation.
Check initial condition: \(f(0) = 0 + 0 + 4 = 4\). Both conditions are satisfied.

## Explanation
Part (a): Direct integration of a first-derivative expression gives the general solution plus an arbitrary constant.
Part (b): The initial condition fixes the constant, producing a unique particular solution.
Part (c): Verification confirms the candidate satisfies the defining equation and condition.
