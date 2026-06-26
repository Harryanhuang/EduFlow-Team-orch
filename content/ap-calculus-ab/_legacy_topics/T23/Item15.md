---
id: T23-Item15
difficulty: C
calculator: calc
type: frq
---
The rate of change of a chemical concentration $C(t)$ (in mol/L) is given by the differential equation
$$\dfrac{dC}{dt} = -0.1C + 2$$
where $t$ is in hours.

**(a)** Find the equilibrium concentration and determine if it is stable or unstable.

**(b)** Solve the differential equation with initial condition $C(0) = 0$.

**(c)** Sketch the solution curve $C(t)$, showing the equilibrium solution and the initial condition. Include horizontal asymptotes.

**(d)** After how many hours will the concentration reach 15 mol/L?

## Answer
**(a)** Setting $dC/dt = 0$:
$$0 = -0.1C + 2$$
$$C = 20 \text{ mol/L}$$

This is a stable equilibrium. For $C < 20$, $dC/dt > 0$ (concentration increases toward 20). For $C > 20$, $dC/dt < 0$ (concentration decreases toward 20).

**(b)** This is a linear differential equation. Using an integrating factor:
$$\dfrac{dC}{dt} + 0.1C = 2$$
$$\mu(t) = e^{\int 0.1\,dt} = e^{0.1t}$$

$$(Ce^{0.1t})' = 2e^{0.1t}$$
$$Ce^{0.1t} = 20e^{0.1t} + C_0$$

Using $C(0) = 0$:
$$0 = 20 + C_0 \implies C_0 = -20$$

$$C(t) = 20 - 20e^{-0.1t} = 20(1 - e^{-0.1t})$$

**(c)** The solution curve starts at $C(0) = 0$ and approaches $C = 20$ as $t \to \infty$. The equilibrium $C = 20$ is a horizontal asymptote.

Key features:
- $C'(t) > 0$ for all $t > 0$ (always increasing)
- $\lim_{t \to \infty} C(t) = 20$ (horizontal asymptote at $y = 20$)
- $C(t) < 20$ for all finite $t$

**(d)** Set $C(t) = 15$:
$$15 = 20(1 - e^{-0.1t})$$
$$0.75 = 1 - e^{-0.1t}$$
$$e^{-0.1t} = 0.25$$
$$-0.1t = \ln(0.25) = -\ln 4$$
$$t = \dfrac{\ln 4}{0.1} = 10\ln 4 \approx 13.86 \text{ hours}$$

## Explanation
This is a linear differential equation with a constant input term. The equilibrium is found by setting the derivative to zero. The solution shows exponential approach to equilibrium, a common pattern in mixing problems and other applications.
