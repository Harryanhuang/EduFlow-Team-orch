---
id: T08-Item14
difficulty: C
calculator: calc
type: frq
---
The temperature T (in degrees Celsius) of a chemical reaction at time t minutes is modeled by T(t) = 20 + 15*arctan(0.5t).

(a) Find T'(t), the rate of temperature change.
(b) At what rate is the temperature changing at t = 2 minutes? Round to three decimal places.
(c) Is the temperature increasing or decreasing at t = 2? Justify.

## Answer
(a) T'(t) = 15 * 0.5/(1 + (0.5t)^2) = 7.5/(1 + 0.25t^2)
(b) T'(2) = 7.5/(1 + 0.25*4) = 7.5/2 = 3.750 degrees per minute
(c) Increasing, because T'(2) = 3.750 > 0.

## Explanation
(a) d/dt[arctan(0.5t)] = 1/(1 + (0.5t)^2) * 0.5 = 0.5/(1 + 0.25t^2). Multiply by 15: T'(t) = 15 * 0.5/(1 + 0.25t^2) = 7.5/(1 + 0.25t^2).
(b) Substitute t = 2: T'(2) = 7.5/(1 + 0.25*4) = 7.5/2 = 3.750.
(c) Since T'(2) > 0, the temperature is increasing at t = 2.
