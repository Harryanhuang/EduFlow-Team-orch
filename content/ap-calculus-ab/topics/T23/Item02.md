---
id: T23-Item02
difficulty: F
calculator: no-calc
type: mcq
---
A population grows according to $\dfrac{dP}{dt} = 0.03P$. If $P(0) = 500$, what is $P(t)$?

A) $P(t) = 500e^{0.03t}$

B) $P(t) = 500 + 0.03t$

C) $P(t) = 500e^{-0.03t}$

D) $P(t) = 500(1.03)^t$

## Answer
A

## Explanation
Separating variables: $dP/P = 0.03\,dt$. Integrating gives $\ln|P| = 0.03t + C$. Using $P(0) = 500$: $\ln(500) = C$. So $\ln|P| = 0.03t + \ln(500)$, which means $P(t) = 500e^{0.03t}$. Option D would be discrete annual compounding, not continuous exponential growth.
