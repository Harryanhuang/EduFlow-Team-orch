---
id: T22-Item09
difficulty: S
calculator: calc
type: frq
---
A bacteria culture grows at a rate proportional to the number of bacteria present. At noon on a particular day, there are 500 bacteria. At 2:00 PM, there are 800 bacteria.

**(a)** Write a differential equation that models the growth of the bacteria culture.

**(b)** Solve the differential equation to find the number of bacteria as a function of time \(t\) (in hours after noon).

**(c)** According to the model, how many bacteria are present at 5:00 PM?

## Answer
**(a)** Let \(B(t)\) be the number of bacteria at time \(t\). The growth rate is proportional to the population:
\[\frac{dB}{dt} = kB\]
where \(k\) is the growth constant.

**(b)** Solve by separation of variables:
\[\frac{dB}{B} = k\,dt\]
\[\ln B = kt + C\]
\[B(t) = Ae^{kt}\]
Use \(B(0) = 500\): \(A = 500\), so \(B(t) = 500e^{kt}\).
Use \(B(2) = 800\): \(800 = 500e^{2k}\)
\[\frac{8}{5} = e^{2k} \implies 2k = \ln\left(\frac{8}{5}\right) \implies k = \frac{1}{2}\ln\left(\frac{8}{5}\right)\]
\[B(t) = 500e^{\frac{t}{2}\ln(8/5)} = 500\left(\frac{8}{5}\right)^{t/2}\]

**(c)** At 5:00 PM, \(t = 5\):
\[B(5) = 500\left(\frac{8}{5}\right)^{5/2} = 500\left(\frac{8}{5}\right)^{2.5}\]
\[\left(\frac{8}{5}\right)^{2.5} = \left(\frac{8}{5}\right)^{2} \cdot \sqrt{\frac{8}{5}} = \frac{64}{25} \cdot \sqrt{1.6} \approx 2.56 \cdot 1.2649 \approx 3.238\]
\[B(5) \approx 500 \times 3.238 \approx 1619\]
Approximately 1,619 bacteria.

## Explanation
This is a classic exponential growth model. The proportionality constant \(k\) is determined from the two data points, then used to predict the population at a future time.
