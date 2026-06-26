---
id: T08-Item11
difficulty: S
calculator: calc
type: frq
---
Let h(x) = (arcsin(x))^2. Find h'(x) and evaluate h'(1/2).

## Answer
h'(x) = 2*arcsin(x)/sqrt(1 - x^2); h'(1/2) = 2*arcsin(1/2)/sqrt(1 - 1/4) = 2*(pi/6)/sqrt(3/4) = (pi/3)/(sqrt(3)/2) = 2*pi/(3*sqrt(3)) = 2*pi*sqrt(3)/9

## Explanation
Apply the chain rule: outer is u^2, inner is u = arcsin(x). h'(x) = 2*arcsin(x) * d/dx[arcsin(x)] = 2*arcsin(x) * 1/sqrt(1 - x^2) = 2*arcsin(x)/sqrt(1 - x^2).
At x = 1/2: arcsin(1/2) = pi/6, sqrt(1 - 1/4) = sqrt(3/4) = sqrt(3)/2. So h'(1/2) = 2*(pi/6)/(sqrt(3)/2) = (pi/3) * 2/sqrt(3) = 2*pi/(3*sqrt(3)).
