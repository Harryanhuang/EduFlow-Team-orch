---
id: T12-Item14
difficulty: C
calculator: calc
type: frq
---
The rate at which people enter an amusement park is modeled by $E(t) = 15600 / (t^2 - 24t + 160)$ and the rate at which people leave is modeled by $L(t) = 9890 / (t^2 - 38t + 370)$, both measured in people per hour, for $9 \leq t \leq 23$, where $t$ is the number of hours after midnight. At $t = 9$, there are no people in the park.

(a) To the nearest whole number, how many people have entered the park by $t = 17$ (5:00 PM)?
(b) At time $t = 13$, is the number of people in the park increasing or decreasing? Justify.
(c) At what time $t$ does the number of people in the park reach its maximum? Justify.

## Answer
(a) People entered = $\int_9^{17} E(t)\, dt = \int_9^{17} \frac{15600}{t^2 - 24t + 160}\, dt$. Using a calculator: this evaluates to approximately 6004 people.

(b) The net rate of change of people in the park is $E(t) - L(t)$. At $t = 13$: $E(13) = 15600/(169 - 312 + 160) = 15600/17 \approx 917.6$ and $L(13) = 9890/(169 - 494 + 370) = 9890/45 \approx 219.8$. Since $E(13) > L(13)$, the net rate is positive, so the number of people is increasing.

(c) The number of people is maximized when the net rate changes from positive to negative, i.e., when $E(t) = L(t)$. Setting $15600/(t^2 - 24t + 160) = 9890/(t^2 - 38t + 370)$ and solving with a calculator gives $t \approx 19.612$ hours (approximately 7:37 PM). Before this time, $E(t) > L(t)$; after, $E(t) < L(t)$.

## Explanation
This is a classic AP-style contextual rate problem with a calculator. Part (a) requires a definite integral. Part (b) tests the interpretation of $E(t) - L(t)$ as the net rate. Part (c) requires finding where the net rate crosses zero and verifying it's a maximum by checking the sign change.
