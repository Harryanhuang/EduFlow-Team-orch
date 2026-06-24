---
id: T13-Item15
difficulty: C
calculator: calc
type: frq
---
A particle moves along the curve $x^2 + 3xy + y^2 = 13$. At the instant when $x = 2$, $y = 1$, and $\frac{dy}{dt} = 2$ units/s:

(a) Find $\frac{dx}{dt}$ at $(2, 1)$.

(b) Find $\frac{d^2x}{dt^2}$ at $(2, 1)$, given that $\frac{d^2y}{dt^2} = -1$ at this instant.

(c) Is the particle moving toward, away from, or parallel to the line $y = x$ at this instant? Justify.

## Answer
(a) $\frac{dx}{dt} = -\frac{16}{7}$ units/s

(b) $\frac{d^2x}{dt^2} = \frac{832}{343}$ units/s$^2$

(c) $\frac{d}{dt}(y - x) = \frac{30}{7} > 0$, so $y - x$ is increasing. At $(2, 1)$, $y - x = -1 < 0$, so the particle is moving toward the line $y = x$.

## Explanation
(a) Differentiating $x^2 + 3xy + y^2 = 13$ with respect to $t$:
$2x\frac{dx}{dt} + 3x\frac{dy}{dt} + 3y\frac{dx}{dt} + 2y\frac{dy}{dt} = 0$
$\implies (2x + 3y)\frac{dx}{dt} + (3x + 2y)\frac{dy}{dt} = 0$

At $(2, 1)$: $(4 + 3)\frac{dx}{dt} + (6 + 2)(2) = 0$
$7\frac{dx}{dt} + 16 = 0 \implies \frac{dx}{dt} = -\frac{16}{7}$

(b) Differentiate the related-rates equation again:
$\left(2\frac{dx}{dt}+3\frac{dy}{dt}\right)\frac{dx}{dt} + (2x+3y)\frac{d^2x}{dt^2} + \left(3\frac{dx}{dt}+2\frac{dy}{dt}\right)\frac{dy}{dt} + (3x+2y)\frac{d^2y}{dt^2} = 0$

At $(2,1)$ with $2x+3y=7$, $3x+2y=8$, $\frac{dx}{dt}=-\frac{16}{7}$, $\frac{dy}{dt}=2$, $\frac{d^2y}{dt^2}=-1$:
- First group: $\left(-\frac{32}{7}+6\right)\left(-\frac{16}{7}\right) + 7\frac{d^2x}{dt^2} = \frac{10}{7}\cdot\left(-\frac{16}{7}\right) + 7\frac{d^2x}{dt^2} = -\frac{160}{49} + 7\frac{d^2x}{dt^2}$.
- Second group: $\left(-\frac{48}{7}+4\right)(2) + 8(-1) = -\frac{20}{7}\cdot 2 - 8 = -\frac{40}{7} - 8 = -\frac{96}{7}$.

Summing: $-\frac{160}{49} - \frac{96}{7} + 7\frac{d^2x}{dt^2} = 0 \implies -\frac{832}{49} + 7\frac{d^2x}{dt^2} = 0 \implies \frac{d^2x}{dt^2} = \frac{832}{343}$.

(c) $\frac{d}{dt}(y-x) = \frac{dy}{dt} - \frac{dx}{dt} = 2 - \left(-\frac{16}{7}\right) = \frac{30}{7} > 0$, and $y - x = 1 - 2 = -1 < 0$. Since $y - x$ is negative and increasing toward 0, the particle is moving toward the line $y = x$.
