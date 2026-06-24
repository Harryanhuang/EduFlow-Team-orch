---
id: T05-Item16
difficulty: C
calculator: calc
type: frq
---
The temperature $T(t)$ of a cup of coffee (in degrees Fahrenheit) is recorded at various times $t$ (in minutes) after being poured.

| $t$ (min) | 0   | 2   | 5   | 8   | 10  | 12  |
|-----------|-----|-----|-----|-----|-----|-----|
| $T(t)$ (deg F) | 180 | 162 | 140 | 122 | 113 | 106 |

(a) Estimate $T'(5)$ using the data in the table. Include appropriate units.

(b) Interpret the meaning of your answer from part (a) in the context of the problem.

(c) Estimate the average rate of change of temperature over the interval $[0, 12]$. How does this compare with the instantaneous rate at $t = 5$?

## Answer
(a) Using the symmetric difference quotient with the closest surrounding data points:
$$T'(5) \approx \frac{T(8) - T(2)}{8 - 2} = \frac{122 - 162}{6} = \frac{-40}{6} \approx -6.667 \text{ deg F/min}$$

(b) At $t = 5$ minutes after the coffee was poured, the temperature is decreasing at a rate of approximately 6.67 degrees Fahrenheit per minute. The negative sign indicates the coffee is cooling.

(c) Average rate of change over $[0, 12]$:
$$\frac{T(12) - T(0)}{12 - 0} = \frac{106 - 180}{12} = \frac{-74}{12} \approx -6.167 \text{ deg F/min}$$

The instantaneous rate at $t = 5$ (approximately $-6.67$) is more negative (faster cooling) than the overall average rate ($-6.17$). This is consistent with Newton's Law of Cooling: the coffee cools faster when it is hotter (early times) and slows down as it approaches room temperature.

## Explanation
This problem tests the interpretation of the derivative as an instantaneous rate of change in a contextual setting. Students must compute a symmetric difference quotient, state units correctly, and compare the instantaneous rate to the average rate. The physics context adds realism and reinforces that derivatives represent real-world rates.
