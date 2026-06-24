---
id: T13-Item16
difficulty: C
calculator: no-calc
type: frq
---
A 25-foot ladder rests against a vertical wall. The bottom of the ladder slides away from the wall at a rate of 5 ft/s.

(a) How fast is the top of the ladder sliding down the wall when the bottom is 15 feet from the wall?

(b) The angle $\theta$ between the ladder and the ground satisfies $\cos\theta = \frac{x}{25}$. Find $\frac{d\theta}{dt}$ at the instant when $x = 15$ feet. Express your answer in radians per second.

(c) At the instant found in part (b), is the angle $\theta$ increasing or decreasing? Justify your answer.

## Answer
(a) $\frac{dy}{dt} = -4$ ft/s

(b) $\frac{d\theta}{dt} = -\frac{1}{4}$ rad/s

(c) $\theta$ is decreasing, since $\frac{d\theta}{dt} < 0$.

## Explanation
(a) $x^2 + y^2 = 625$. At $x = 15$: $y = \sqrt{400} = 20$.
Differentiating: $2x\frac{dx}{dt} + 2y\frac{dy}{dt} = 0$.
$2(15)(5) + 2(20)\frac{dy}{dt} = 0 \implies 150 + 40\frac{dy}{dt} = 0 \implies \frac{dy}{dt} = -4$ ft/s.

(b) $\cos\theta = \frac{x}{25}$. Differentiating with respect to $t$:
$-\sin\theta\frac{d\theta}{dt} = \frac{1}{25}\frac{dx}{dt}$.
At $x = 15$, $y = 20$, so $\sin\theta = \frac{y}{25} = \frac{20}{25} = \frac{4}{5}$.
$-\frac{4}{5}\frac{d\theta}{dt} = \frac{5}{25} = \frac{1}{5}$.
Solving: $\frac{d\theta}{dt} = -\frac{1}{5} \cdot \frac{5}{4} = -\frac{1}{4}$ rad/s.

(c) Since $\frac{d\theta}{dt} < 0$, the angle $\theta$ is decreasing.
