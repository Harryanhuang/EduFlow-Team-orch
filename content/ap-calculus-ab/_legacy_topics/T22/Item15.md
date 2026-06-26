---
id: T22-Item15
difficulty: C
calculator: calc
type: frq
---
A tank initially contains 100 gallons of brine (salt water) containing 50 pounds of dissolved salt. Fresh water flows into the tank at a rate of 3 gallons per minute, and the mixture flows out at the same rate, keeping the volume constant.

**(a)** Write a differential equation that models the amount of salt \(S(t)\) (in pounds) in the tank at time \(t\) minutes.

**(b)** Solve the differential equation to find \(S(t)\).

**(c)** How much salt remains in the tank after 20 minutes?

**(d)** In the long run, how much salt remains in the tank? Explain your answer.

## Answer
**(a)** The rate of change of salt is:
\[\frac{dS}{dt} = (\text{rate in}) - (\text{rate out})\]
Fresh water has 0 lb/gal, so rate in = 0.
The outflow concentration is \(\frac{S}{100}\) lb/gal at rate 3 gal/min, so rate out = \(3 \cdot \frac{S}{100} = \frac{3S}{100}\).
Thus:
\[\frac{dS}{dt} = -\frac{3S}{100}\]

**(b)** Separate and solve:
\[\frac{dS}{S} = -\frac{3}{100}\,dt\]
\[\ln S = -\frac{3t}{100} + C\]
\[S(t) = Ae^{-3t/100}\]
Use \(S(0) = 50\): \(A = 50\), so \(S(t) = 50e^{-3t/100}\).

**(c)** At \(t = 20\):
\[S(20) = 50e^{-3(20)/100} = 50e^{-0.6} \approx 50 \times 0.5488 \approx 27.4\text{ lb}\]

**(d)** As \(t \to \infty\), \(e^{-3t/100} \to 0\), so \(S(t) \to 0\).
Since only pure water enters and the mixture leaves at the same rate, eventually all salt is flushed out of the tank.

## Explanation
This is a mixing problem with no salt entering the tank. The differential equation \(\frac{dS}{dt} = -\frac{3}{100}S\) has an exponential decay solution, confirming the intuitive result that the salt asymptotically approaches zero.
