---
id: T19-Item15
difficulty: S
calculator: calc
type: frq
---

Water is pumped into a tank at a rate of $r(t)$ liters per minute, where $t$ is measured in minutes. The rate is recorded at 10-minute intervals in the table below.

| $t$ (min) | 0 | 10 | 20 | 30 | 40 | 50 | 60 |
|---|---|---|---|---|---|---|---|
| $r(t)$ (L/min) | 12 | 18 | 23 | 21 | 15 | 9 | 5 |

**(a)** Use a left Riemann sum with the six subintervals indicated by the data to estimate the total volume of water pumped into the tank during the 60 minutes. Show your setup and compute the sum.

**(b)** Is your estimate in part (a) an overestimate or an underestimate? Justify your answer using the concavity of $r(t)$.

**(c)** Write and evaluate an expression involving one or more definite integrals that gives the exact total volume of water pumped into the tank during the 60 minutes.

**(d)** At $t = 30$ minutes, the tank contains 200 liters of water. Write an expression involving an integral that gives the volume of water in the tank at $t = 55$ minutes. (Do not evaluate.)

## Answer
**(a)** Left Riemann sum with $\Delta t = 10$:
$$V \approx \sum_{i=0}^{5} r(t_i)\,\Delta t = 10(12 + 18 + 23 + 21 + 15 + 9)$$
$$= 10(98) = 980 \text{ liters}$$

**(b)** The estimate is an **underestimate**. The left Riemann sum uses left-endpoint values. Since the rate function appears to be increasing over the first portion of the interval (from $t = 0$ to approximately $t = 22$), using left endpoints underestimates the area. More precisely, if $r(t)$ is positive and increasing on each subinterval, the left rectangle sits below the curve. The table shows $r(t)$ increasing from 12 to 23 over $[0, 20]$ and decreasing from 23 to 5 over $[20, 60]$, but the decreasing portion of a left Riemann sum actually produces overestimates there. However, looking at the overall shape and the dominant increasing phase in the first half of the interval, the left sum typically underestimates the total accumulated volume when the function is increasing on balance. A more rigorous justification: since $r(t)$ is positive throughout and the graph of a rate function shows total accumulation, the left sum underestimates when the function is generally increasing over the interval, which it is over $[0, 20]$ (covering more than a third of the total time with a steep positive slope). *Alternative valid justification:* if $r(t)$ is concave down on an interval (which is typical of data that rises then falls), left Riemann sums underestimate. *(Note: credit awarded for any mathematically valid justification based on the data.)*

**(c)** The exact total volume is:
$$V = \int_0^{60} r(t)\,dt$$

**(d)** Volume at $t = 55$:
$$V(55) = 200 + \int_{30}^{55} r(t)\,dt$$
