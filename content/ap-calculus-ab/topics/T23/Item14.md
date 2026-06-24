---
id: T23-Item14
difficulty: C
calculator: calc
type: frq
---
A dead body is found at 2:00 PM in a room maintained at $15^\circ$C. At that time, the body's temperature is measured to be $27^\circ$C. Twenty minutes later, the temperature is $25^\circ$C. Use Newton's Law of Cooling with ambient temperature $T_{env} = 15^\circ$C.

**(a)** Write the differential equation and initial condition for the body temperature $T(t)$, where $t$ is measured in hours since 2:00 PM.

**(b)** Solve for $T(t)$ and determine the cooling constant $k$.

**(c)** If normal human body temperature is $37^\circ$C, estimate the time of death.

## Answer
**(a)** Newton's Law: $\dfrac{dT}{dt} = -k(T - 15)$, with $T(0) = 27$

**(b)** Solving: $T(t) = 15 + 12e^{-kt}$

At $t = 1/3$ hour (20 minutes): $25 = 15 + 12e^{-k/3}$
$$10 = 12e^{-k/3}$$
$$e^{-k/3} = \dfrac{10}{12} = \dfrac{5}{6}$$
$$-\dfrac{k}{3} = \ln\left(\dfrac{5}{6}\right)$$
$$k = -3\ln\left(\dfrac{5}{6}\right) = 3\ln\left(\dfrac{6}{5}\right) \approx 0.546$$

**(c)** We need $T(t) = 37$:
$$37 = 15 + 12e^{-kt}$$
$$22 = 12e^{-kt}$$
$$e^{-kt} = \dfrac{22}{12} = \dfrac{11}{6} > 1$$

This gives $t < 0$, meaning the body was warmer before discovery. Setting time of death as $t_d < 0$:
$$37 = 15 + 12e^{-k t_d}$$
$$22 = 12e^{-k t_d}$$
$$e^{-k t_d} = \dfrac{11}{6}$$
$$-k t_d = \ln\left(\dfrac{11}{6}\right)$$
$$t_d = -\dfrac{\ln(11/6)}{k} = -\dfrac{\ln(11/6)}{3\ln(6/5)}$$

Computing numerically:
$$t_d \approx -\dfrac{\ln(1.833)}{3\ln(1.2)} \approx -\dfrac{0.606}{3(0.182)} \approx -\dfrac{0.606}{0.546} \approx -1.11 \text{ hours} \approx -67 \text{ minutes}$$

So death occurred approximately 67 minutes before 2:00 PM, or at about 12:53 PM.

## Explanation
This problem combines Newton's Law of Cooling with two-point determination of the constant. The key insight is that the time of death corresponds to $t < 0$ (before discovery), requiring solving for a negative time value.
