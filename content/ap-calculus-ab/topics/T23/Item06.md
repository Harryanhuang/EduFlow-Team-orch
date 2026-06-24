---
id: T23-Item06
difficulty: S
calculator: no-calc
type: mcq
---
A sample of 500 grams of a radioactive substance decays according to $\dfrac{dA}{dt} = -0.02A$. How much remains after 50 years?

A) $500e^{-1}$ grams

B) $500e^{-0.5}$ grams

C) $500(0.98)^{50}$ grams

D) $500 - 0.02(50)$ grams

## Answer
A

## Explanation
Solving $dA/dt = -0.02A$ with $A(0) = 500$: Separating variables and integrating gives $\ln|A| = -0.02t + C$. Using $A(0) = 500$: $C = \ln(500)$. So $A(t) = 500e^{-0.02t}$. At $t = 50$: $A(50) = 500e^{-0.02(50)} = 500e^{-1}$ grams. Option B uses $e^{-0.5}$ (25 years). Option C uses discrete decay. Option D uses linear decay, which is incorrect for exponential decay.
