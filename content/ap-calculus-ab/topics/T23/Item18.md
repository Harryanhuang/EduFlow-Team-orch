---
id: T23-Item18
difficulty: C
calculator: calc
type: frq
---
A tank contains 100 liters of water. Brine (salt water) containing 0.3 kg of salt per liter flows into the tank at a rate of 4 L/min. The mixture flows out at the same rate, and the tank is kept well-stirred.

**(a)** Write the differential equation for $S(t)$, the amount of salt (in kg) in the tank after $t$ minutes.

**(b)** Find $S(t)$ given that initially there is no salt in the tank.

**(c)** What is the limiting amount of salt in the tank as $t \to \infty$?

**(d)** How long does it take for the salt content to reach 20 kg?

## Answer
**(a)** Rate in: $(0.3 \text{ kg/L}) \times (4 \text{ L/min}) = 1.2$ kg/min

Rate out: $(S/100 \text{ kg/L}) \times (4 \text{ L/min}) = \dfrac{4S}{100} = \dfrac{S}{25}$ kg/min

$$\dfrac{dS}{dt} = 1.2 - \dfrac{S}{25}$$

**(b)** This is a linear differential equation:
$$\dfrac{dS}{dt} + \dfrac{1}{25}S = 1.2$$

Integrating factor: $\mu(t) = e^{t/25}$

$$(Se^{t/25})' = 1.2e^{t/25}$$
$$Se^{t/25} = 1.2 \cdot 25e^{t/25} + C = 30e^{t/25} + C$$
$$S(t) = 30 + Ce^{-t/25}$$

Using $S(0) = 0$:
$$0 = 30 + C \implies C = -30$$

$$S(t) = 30(1 - e^{-t/25})$$

**(c)** As $t \to \infty$, $e^{-t/25} \to 0$:
$$\lim_{t \to \infty} S(t) = 30 \text{ kg}$$

This makes sense: in steady state, the inflow concentration (0.3 kg/L) times the tank volume (100 L) gives $0.3 \times 100 = 30$ kg of salt.

**(d)** Set $S(t) = 20$:
$$20 = 30(1 - e^{-t/25})$$
$$\dfrac{2}{3} = 1 - e^{-t/25}$$
$$e^{-t/25} = \dfrac{1}{3}$$
$$-\dfrac{t}{25} = \ln\left(\dfrac{1}{3}\right) = -\ln 3$$
$$t = 25\ln 3 \approx 27.5 \text{ minutes}$$

## Explanation
This is a classic mixing problem. The key insight is that both the inflow and outflow rates are equal (4 L/min), maintaining constant volume. The equilibrium $S^* = 30$ kg comes from the steady-state condition $dS/dt = 0$, which gives $1.2 - S/25 = 0$, so $S = 30$.
