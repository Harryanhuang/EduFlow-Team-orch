---
id: T22-Item13
difficulty: S
calculator: calc
type: frq
---
A metal ball at temperature \(120^{\circ}\)F is placed in a room where the ambient temperature is \(70^{\circ}\)F. According to Newton's Law of Cooling, the temperature of the ball changes at a rate proportional to the difference between its temperature and the ambient temperature.

**(a)** Write a differential equation that models the temperature \(T(t)\) of the ball at time \(t\) minutes.

**(b)** If the temperature of the ball drops to \(90^{\circ}\)F in 10 minutes, find the particular solution for \(T(t)\).

**(c)** How long will it take for the ball's temperature to reach \(75^{\circ}\)F?

## Answer
**(a)** Newton's Law of Cooling:
\[\frac{dT}{dt} = -k(T - 70)\]
where \(k > 0\) is the cooling constant.

**(b)** Separate and integrate:
\[\frac{dT}{T-70} = -k\,dt\]
\[\ln|T-70| = -kt + C\]
\[T(t) - 70 = Ae^{-kt} \implies T(t) = 70 + Ae^{-kt}\]
Use \(T(0) = 120\): \(120 = 70 + A \implies A = 50\), so \(T(t) = 70 + 50e^{-kt}\).
Use \(T(10) = 90\): \(90 = 70 + 50e^{-10k}\)
\[20 = 50e^{-10k} \implies e^{-10k} = \frac{2}{5} \implies -10k = \ln(0.4)\]
\[k = -\frac{1}{10}\ln(0.4) = \frac{\ln(2.5)}{10}\]
\[T(t) = 70 + 50e^{-(\ln(2.5)/10)t} = 70 + 50 \cdot (0.4)^{t/10}\]

**(c)** Set \(T(t) = 75\):
\[75 = 70 + 50(0.4)^{t/10}\]
\[5 = 50(0.4)^{t/10} \implies 0.1 = (0.4)^{t/10}\]
\[\ln(0.1) = \frac{t}{10}\ln(0.4) \implies t = 10\frac{\ln(0.1)}{\ln(0.4)} = 10\frac{-\ln 10}{-\ln 0.4} = 10\frac{\ln 10}{\ln(2.5)}\]
\[\ln 10 \approx 2.3026,\quad \ln(2.5) \approx 0.9163 \implies t \approx 10 \times 2.513 \approx 25.1\text{ minutes}\]

## Explanation
Newton's Law of Cooling is a standard first-order linear differential equation with solution \(T(t) = T_{\text{ambient}} + Ce^{-kt}\). The constant \(k\) is determined from the given data, then used to find the time to reach a target temperature.
