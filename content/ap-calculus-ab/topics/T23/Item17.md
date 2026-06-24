---
id: T23-Item17
difficulty: C
calculator: calc
type: frq
---
A radioactive isotope has an initial mass of 50 grams and decays with a half-life of 10 years. At the same time, new material is being created from a generator at a constant rate of 2 grams per year.

**(a)** Write the differential equation for the mass $M(t)$ of the radioactive material.

**(b)** Find the particular solution satisfying $M(0) = 50$.

**(c)** Find the limiting value $\displaystyle\lim_{t \to \infty} M(t)$ and interpret this result.

**(d)** At what time is the mass at its maximum?

## Answer
**(a)** The decay follows $dM/dt = -kM$ with $k = \ln(2)/10$. With constant production rate $P = 2$:
$$\dfrac{dM}{dt} = -\dfrac{\ln 2}{10}M + 2$$

**(b)** This is a linear differential equation. Solving:
$$\dfrac{dM}{dt} + \dfrac{\ln 2}{10}M = 2$$

Integrating factor: $\mu(t) = e^{(\ln 2/10)t} = 2^{t/10}$

$$(M \cdot 2^{t/10})' = 2 \cdot 2^{t/10}$$
$$M \cdot 2^{t/10} = \dfrac{2 \cdot 10}{\ln 2}2^{t/10} + C = \dfrac{20}{\ln 2}2^{t/10} + C$$

$$M(t) = \dfrac{20}{\ln 2} + Ce^{-(\ln 2/10)t} = \dfrac{20}{\ln 2} + Ce^{-0.0693t}$$

Using $M(0) = 50$:
$$50 = \dfrac{20}{\ln 2} + C$$
$$C = 50 - \dfrac{20}{\ln 2} \approx 50 - 28.85 = 21.15$$

So:
$$M(t) = \dfrac{20}{\ln 2} + \left(50 - \dfrac{20}{\ln 2}\right)2^{-t/10}$$

**(c)** As $t \to \infty$, $2^{-t/10} \to 0$, so:
$$\lim_{t \to \infty} M(t) = \dfrac{20}{\ln 2} \approx 28.85 \text{ grams}$$

This is the equilibrium mass where the decay rate equals the production rate. The isotope is being produced and decaying simultaneously, approaching a steady state.

**(d)** Since $M(0) = 50 > 28.85$, the mass is initially above equilibrium and decreases monotonically toward it. Therefore, the maximum mass occurs at $t = 0$, with maximum value $M_{max} = 50$ grams.

## Explanation
This is a linear differential equation with competing decay and production. The equilibrium solution $M^* = 20/\ln 2$ represents the steady state. Since the initial mass exceeds equilibrium, the mass decreases monotonically toward it.
