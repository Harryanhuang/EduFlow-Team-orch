---
id: T13-Item18
difficulty: C
calculator: calc
type: frq
---
A spherical balloon is being inflated at a constant rate of 20 cm$^3$/s. At the same time, air is leaking out through a small hole at a rate proportional to the square of the balloon's radius. When the radius is 3 cm, the leak rate is 1 cm$^3$/s.

(a) Write an expression for the net rate of change of volume $\frac{dV}{dt}$ as a function of $r$.

(b) Find $\frac{dr}{dt}$ when $r = 3$ cm.

(c) Find $\frac{d^2r}{dt^2}$ when $r = 3$ cm. Is the radius increasing at an increasing rate or at a decreasing rate? Justify.

(d) Compare $\left|\frac{dr}{dt}\right|$ at $r = 2$ cm and at $r = 3$ cm. At which radius is the balloon expanding faster?

## Answer
(a) $\frac{dV}{dt} = 20 - \frac{r^2}{9}$ cm$^3$/s

(b) $\frac{dr}{dt} = \frac{19}{36\pi}$ cm/s

(c) $\frac{d^2r}{dt^2} = -\frac{19+684\pi^2}{1944\pi^2} < 0$. The radius is increasing at a decreasing rate.

(d) At $r = 2$ cm: $\left|\frac{dr}{dt}\right| = \frac{11}{9\pi} \approx 0.389$ cm/s. At $r = 3$ cm: $\left|\frac{dr}{dt}\right| = \frac{19}{36\pi} \approx 0.168$ cm/s. The balloon is expanding faster at $r = 2$ cm.

## Explanation
(a) Leak rate $L = kr^2$. At $r = 3$, $L = 1$, so $1 = k(9) \implies k = \frac{1}{9}$. Thus $L = \frac{r^2}{9}$ and $\frac{dV}{dt} = 20 - \frac{r^2}{9}$.

(b) $V = \frac{4}{3}\pi r^3 \implies \frac{dV}{dt} = 4\pi r^2\frac{dr}{dt}$. At $r = 3$: $4\pi(9)\frac{dr}{dt} = 20 - 1 = 19 \implies \frac{dr}{dt} = \frac{19}{36\pi}$.

(c) Differentiating $4\pi r^2\frac{dr}{dt} = 20 - \frac{r^2}{9}$ with respect to $t$:
$8\pi r\frac{dr}{dt} + 4\pi r^2\frac{d^2r}{dt^2} = -\frac{2r}{9}\frac{dr}{dt}$.

At $r = 3$, $\frac{dr}{dt} = \frac{19}{36\pi}$:
$8\pi(3)\frac{19}{36\pi} + 4\pi(9)\frac{d^2r}{dt^2} = -\frac{2(3)}{9}\frac{19}{36\pi}$
$\frac{152}{12} + 36\pi\frac{d^2r}{dt^2} = -\frac{19}{54\pi}$
$36\pi\frac{d^2r}{dt^2} = -\frac{19}{54\pi} - \frac{38}{3} = -\frac{19 + 684\pi^2}{54\pi}$
$\frac{d^2r}{dt^2} = -\frac{19 + 684\pi^2}{1944\pi^2} < 0$.

Since $\frac{d^2r}{dt^2} < 0$, the radius is increasing at a decreasing rate.

(d) $\frac{dr}{dt} = \frac{20 - r^2/9}{4\pi r^2}$.
At $r = 2$: $\frac{dr}{dt} = \frac{20 - 4/9}{16\pi} = \frac{176/9}{16\pi} = \frac{11}{9\pi} \approx 0.389$ cm/s.
At $r = 3$: $\frac{dr}{dt} = \frac{19}{36\pi} \approx 0.168$ cm/s.
The balloon expands faster at $r = 2$ cm.
