---
id: T22-Item17
difficulty: C
calculator: calc
type: frq
---
The rate of change of a certain substance is modeled by the differential equation \(\dfrac{dN}{dt} = (0.05 - 0.0005N)N\), where \(N(t)\) is the amount of the substance at time \(t\).

**(a)** Find all equilibrium solutions and classify each as stable or unstable.

**(b)** Sketch a direction field for this differential equation and describe the long-term behavior of solutions with initial values \(N(0) = 20\) and \(N(0) = 120\).

**(c)** Find the particular solution for \(N(0) = 20\) and compute \(N(10)\).

**(d)** Find \(\displaystyle\lim_{t\to\infty} N(t)\) for any solution with \(N(0) > 0\).

## Answer
**(a)** Set \(\frac{dN}{dt} = 0\):
\[N(0.05 - 0.0005N) = 0 \implies N = 0 \text{ or } 0.05 - 0.0005N = 0 \implies N = 100\]
Equilibria: \(N = 0\) and \(N = 100\).

Classify \(N = 0\): If \(N > 0\) but small, \(\frac{dN}{dt} > 0\) (since \(0.05 - 0.0005N > 0\)), so solutions move away from 0. **Unstable.**
Classify \(N = 100\): Write \(f(N) = (0.05 - 0.0005N)N\). For \(N$ slightly below 100, \(0.05 - 0.0005N > 0\), so \(f(N) > 0\) (increasing toward 100). For \(N\) slightly above 100, \(0.05 - 0.0005N < 0\), so \(f(N) < 0\) (decreasing toward 100). **Stable.**

**(b)** For \(0 < N < 100\): \(\frac{dN}{dt} > 0\) so solutions increase toward 100.
For \(N > 100\): \(\frac{dN}{dt} < 0$ so solutions decrease toward 100.
With \(N(0) = 20\), the solution increases toward 100.
With \(N(0) = 120\), the solution decreases toward 100.

**(c)** Separate:
\[\frac{dN}{N(0.05 - 0.0005N)} = dt\]
\[\frac{dN}{N(0.05 - 0.0005N)} = \frac{dN}{0.05N - 0.0005N^{2}} = dt\]
Partial fractions: \(\frac{1}{N(0.05 - 0.0005N)} = \frac{1}{0.05}\left(\frac{1}{N} + \frac{0.0005}{0.05 - 0.0005N}\right) = 20\left(\frac{1}{N} + \frac{1}{100 - N}\right)\)
So:
\[\int 20\left(\frac{1}{N} + \frac{1}{100-N}\right)dN = \int dt\]
\[20(\ln N - \ln|100-N|) = t + C\]
\[\ln\left(\frac{N}{100-N}\right) = \frac{t + C}{20}\]
\[\frac{N}{100-N} = Ae^{t/20}\]
For \(N(0) = 20\): \(\frac{20}{80} = 0.25 = A\), so:
\[\frac{N}{100-N} = \frac{1}{4}e^{t/20} \implies N = 100\frac{e^{t/20}}{4+e^{t/20}} = \frac{100}{1+4e^{-t/20}}\]
At \(t = 10\): \(N(10) = \frac{100}{1+4e^{-10/20}} = \frac{100}{1+4e^{-0.5}} \approx \frac{100}{1+4(0.6065)} \approx \frac{100}{3.426} \approx 29.2\)

**(d)** As \(t \to \infty\), \(e^{-t/20} \to 0\), so \(N(t) \to \frac{100}{1+0} = 100\).
For any positive initial condition, all solutions are attracted to the stable equilibrium \(N = 100\).

## Explanation
This is a logistic-type differential equation (competition/self-limiting growth). Part (a) uses linearization to classify equilibria. Part (c) uses partial fractions to solve, yielding a logistic-shaped solution curve. The long-term limit is the carrying capacity \(K = 100\).
