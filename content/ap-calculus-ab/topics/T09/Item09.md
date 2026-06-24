---
id: T09-Item09
difficulty: S
calculator: no-calc
type: frq
---
A population of bacteria is modeled by the function

P(t) = 500 · e^(0.03t²)

where P(t) is the number of bacteria and t is the time in hours after the experiment begins.

**(a)** Find P'(t), the rate of change of the population with respect to time.

**(b)** Find the rate of change of the population at t = 10 hours. Give your answer to three decimal places.

**(c)** Interpret the meaning of your answer to part (b) in the context of the problem, including appropriate units.

## Answer

**(a)** Using the chain rule with outer function e^u and inner function u = 0.03t²:

P'(t) = 500 · e^(0.03t²) · d/dt[0.03t²]
      = 500 · e^(0.03t²) · 0.06t
      = **30t · e^(0.03t²)**

**(b)** At t = 10:

P'(10) = 30(10) · e^(0.03 · 100)
       = 300 · e³
       ≈ 300 · 20.085537
       ≈ **6,025.661** bacteria per hour

**(c)** After 10 hours, the bacterial population is **increasing** at a rate of approximately **6,025.661 bacteria per hour**. This means that at the instant t = 10 hours, the population is growing by about 6,026 bacteria each hour.

## Explanation
Part (a) requires the chain rule: d/dt[e^(g(t))] = e^(g(t)) · g'(t). Here g(t) = 0.03t², so g'(t) = 0.06t. Multiplying by the constant 500 gives 500 · 0.06t · e^(0.03t²) = 30t · e^(0.03t²).

Part (b) substitutes t = 10 into the derivative. The exponent evaluates to 0.03 · 100 = 3, so P'(10) = 300 · e³. Using e³ ≈ 20.085537, we get 6,025.661.

Part (c) requires an interpretation statement that includes:
- Direction: "increasing" (since P'(10) > 0)
- Rate value: 6,025.661
- Units: bacteria per hour
- Time reference: "at t = 10 hours" or "after 10 hours"
