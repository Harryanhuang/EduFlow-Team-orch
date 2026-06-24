---
id: T12-Item07
difficulty: S
calculator: calc
type: mcq
---
The volume of water in a reservoir, in megaliters, is modeled by $V(t) = 500 + 200\sin\left(\frac{\pi t}{6}\right)$ for $0 \leq t \leq 24$, where $t$ is measured in hours. At what time $t$ is the volume decreasing most rapidly?

## Options
A) $t = 3$
B) $t = 6$
C) $t = 9$
D) $t = 12$

## Answer
C

## Explanation
The rate of change of volume is $V'(t) = 200 \cdot \frac{\pi}{6} \cos\left(\frac{\pi t}{6}\right) = \frac{100\pi}{3}\cos\left(\frac{\pi t}{6}\right)$. The volume is decreasing most rapidly when $V'(t)$ is most negative, i.e., when $\cos\left(\frac{\pi t}{6}\right) = -1$. This occurs when $\frac{\pi t}{6} = \pi$, so $t = 6$. Wait — checking: at $t = 6$, $\cos(\pi) = -1$, giving $V'(6) = -\frac{100\pi}{3}$. At $t = 9$, $\cos(3\pi/2) = 0$, so $V'(9) = 0$. So the answer is $t = 6$, choice B.
