---
id: T12-Item09
difficulty: S
calculator: no-calc
type: mcq
---
A balloon is being inflated so that its volume $V$ (in cm$^3$) is increasing at a rate of $V'(t) = \frac{12}{\sqrt{t+1}}$ cm$^3$/min. If the balloon contains 50 cm$^3$ of air at $t = 0$, how much air does it contain at $t = 8$ minutes?

## Options
A) 66 cm$^3$
B) 74 cm$^3$
C) 98 cm$^3$
D) 114 cm$^3$

## Answer
C

## Explanation
By the Fundamental Theorem of Calculus: $V(8) = V(0) + \int_0^8 V'(t)\, dt = 50 + \int_0^8 12(t+1)^{-1/2}\, dt$. The antiderivative of $12(t+1)^{-1/2}$ is $24(t+1)^{1/2}$. So $V(8) = 50 + [24\sqrt{t+1}]_0^8 = 50 + 24(3) - 24(1) = 50 + 72 - 24 = 98$ cm$^3$.
