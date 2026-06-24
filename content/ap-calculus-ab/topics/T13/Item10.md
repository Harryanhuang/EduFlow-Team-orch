---
id: T13-Item10
difficulty: S
calculator: no-calc
type: mcq
---
Two cars start from the same intersection. Car A travels east at 40 mph and Car B travels north at 30 mph. How fast is the distance between the cars changing 2 hours after they start?

## Options
A) 40 mph
B) 50 mph
C) 70 mph
D) 100 mph

## Answer
B) 50 mph

## Explanation
Let $x$ = distance of Car A east, $y$ = distance of Car B north, $z$ = distance between them.
By the Pythagorean theorem: $x^2 + y^2 = z^2$.

Differentiating: $2x\frac{dx}{dt} + 2y\frac{dy}{dt} = 2z\frac{dz}{dt}$, so $\frac{dz}{dt} = \frac{x dx/dt + y dy/dt}{z}$.

After 2 hours: $x = 40(2) = 80$, $y = 30(2) = 60$, so $z = \sqrt{80^2 + 60^2} = 100$.

$\frac{dz}{dt} = \frac{80(40) + 60(30)}{100} = \frac{3200 + 1800}{100} = 50$ mph.
