---
id: T23-Item13
difficulty: C
calculator: calc
type: frq
---
A colony of bacteria is grown in a nutrient medium. The population $P(t)$ satisfies the logistic differential equation
$$\dfrac{dP}{dt} = 0.5P\left(1 - \dfrac{P}{2000}\right)$$
where $P$ is the number of bacteria and $t$ is in hours.

**(a)** What are the equilibrium solutions? Classify each as stable or unstable.

**(b)** If $P(0) = 500$, write the solution function $P(t)$.

**(c)** Find $\displaystyle\lim_{t \to \infty} P(t)$.

**(d)** At what time is the population growing fastest?

## Answer
**(a)** Equilibrium solutions occur when $dP/dt = 0$:
- $P = 0$ (stable equilibrium - populations near 0 decrease or stay at 0)
- $P = 2000$ (unstable equilibrium - acts as a threshold; populations above 2000 decrease, below grow toward 2000)

**(b)** The logistic solution with initial condition $P(0) = P_0$ is:
$$P(t) = \dfrac{K}{1 + \left(\dfrac{K - P_0}{P_0}\right)e^{-rt}} = \dfrac{2000}{1 + \left(\dfrac{2000 - 500}{500}\right)e^{-0.5t}} = \dfrac{2000}{1 + 3e^{-0.5t}}$$

**(c)** $\displaystyle\lim_{t \to \infty} P(t) = \dfrac{2000}{1 + 0} = 2000$ (the carrying capacity)

**(d)** The growth rate $dP/dt = 0.5P(1 - P/2000)$ is maximized when $P = K/2 = 1000$ (half the carrying capacity).

Setting $P(t) = 1000$:
$$1000 = \dfrac{2000}{1 + 3e^{-0.5t}}$$
$$1 + 3e^{-0.5t} = 2$$
$$3e^{-0.5t} = 1$$
$$e^{-0.5t} = \dfrac{1}{3}$$
$$-0.5t = -\ln 3$$
$$t = 2\ln 3 \approx 2.197 \text{ hours}$$

## Explanation
This problem tests understanding of the logistic growth model. Part (a) requires setting $dP/dt = 0$ to find equilibria. Part (b) uses the standard logistic solution formula. Part (c) is the long-term limit, which is always the carrying capacity. Part (d) uses calculus to find when growth is maximized: for logistic models, this always occurs at $P = K/2$.
