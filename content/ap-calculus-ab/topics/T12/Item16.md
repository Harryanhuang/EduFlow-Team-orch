---
id: T12-Item16
difficulty: C
calculator: calc
type: frq
---
The temperature of a cup of coffee is modeled by $T(t) = 20 + 70e^{-kt}$ degrees Celsius, where $t$ is measured in minutes and $k > 0$ is a constant. At $t = 0$, the coffee is 90 degrees Celsius, and at $t = 5$, it is 65 degrees Celsius.

(a) Find the value of $k$ to three decimal places.
(b) What is the rate at which the coffee is cooling at $t = 10$? Include units.
(c) At what time $t$ is the coffee cooling at a rate of exactly 1 degree Celsius per minute?
(d) What does $\displaystyle\lim_{t \to \infty} T(t)$ represent in the context of this problem?

## Answer
(a) $T(5) = 20 + 70e^{-5k} = 65 \Rightarrow 70e^{-5k} = 45 \Rightarrow e^{-5k} = 9/14 \Rightarrow -5k = \ln(9/14) \Rightarrow k = -\frac{1}{5}\ln(9/14) = \frac{1}{5}\ln(14/9) \approx 0.088$.

(b) $T'(t) = 70(-k)e^{-kt} = -70ke^{-kt}$. At $t = 10$: $T'(10) = -70(0.088)e^{-0.88} \approx -6.16 \cdot 0.4148 \approx -2.56$ degrees Celsius per minute. The coffee is cooling at approximately 2.56 degrees Celsius per minute.

(c) Set $|T'(t)| = 1$: $70ke^{-kt} = 1 \Rightarrow e^{-kt} = \frac{1}{70k} \Rightarrow -kt = \ln\left(\frac{1}{70k}\right) \Rightarrow t = -\frac{1}{k}\ln\left(\frac{1}{70k}\right)$. With $k \approx 0.088$: $t = -\frac{1}{0.088}\ln\left(\frac{1}{6.16}\right) = -\frac{1}{0.088} \cdot (-1.818) \approx 20.66$ minutes.

(d) $\lim_{t \to \infty} T(t) = 20$. This represents the ambient (room) temperature — the temperature the coffee approaches as it cools indefinitely, consistent with Newton's Law of Cooling.

## Explanation
Part (a) uses given data to solve for the decay constant. Part (b) combines differentiation with contextual interpretation. Part (c) requires solving an exponential equation. Part (d) tests understanding of the horizontal asymptote in the physical context of Newton's Law of Cooling.
