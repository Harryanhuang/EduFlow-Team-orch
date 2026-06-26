---
id: T13-Item13
difficulty: C
calculator: calc
type: frq
---
A right circular cone of height 20 cm and base radius 8 cm is being filled with water at a rate of 15 cm$^3$/s. At the same time, water is leaking out of the cone through a small hole at the vertex at a rate proportional to the square root of the water depth $h$. When $h = 10$ cm, the leak rate is 5 cm$^3$/s.

(a) Find the net rate of change of volume $\frac{dV}{dt}$ when $h = 10$ cm.

(b) Express the leak rate $L$ as a function of $h$ (using the given information).

(c) Write $\frac{dV}{dt}$ in terms of $h$ and $\frac{dh}{dt}$ for any $h$.

(d) Find $\frac{dh}{dt}$ when $h = 10$ cm.

## Answer
(a) Net $\frac{dV}{dt} = 15 - 5 = 10$ cm$^3$/s

(b) $L = k\sqrt{h}$; using $h = 10$, $L = 5$: $5 = k\sqrt{10} \implies k = \frac{5}{\sqrt{10}}$, so $L = \frac{5\sqrt{h}}{\sqrt{10}}$

(c) $V = \frac{1}{3}\pi r^2 h$. By similar triangles: $r = \frac{2h}{5}$, so $V = \frac{4\pi}{75}h^3$.
Thus $\frac{dV}{dt} = \frac{4\pi}{25}h^2 \frac{dh}{dt}$.

(d) At $h = 10$: $\frac{4\pi}{25}(100)\frac{dh}{dt} = 10 \implies \frac{dh}{dt} = \frac{10}{16\pi} = \frac{5}{8\pi} \approx 0.199$ cm/s

## Explanation
(b) $L = k\sqrt{h}$. At $h = 10$, $L = 5$, so $k = \frac{5}{\sqrt{10}}$.
Thus $L(h) = \frac{5\sqrt{h}}{\sqrt{10}}$.

(c) $\frac{r}{h} = \frac{8}{20} = \frac{2}{5}$, so $r = \frac{2h}{5}$.
$V = \frac{1}{3}\pi\left(\frac{2h}{5}\right)^2 h = \frac{4\pi}{75}h^3$.
$\frac{dV}{dt} = \frac{4\pi}{25}h^2 \frac{dh}{dt}$.

(d) At $h = 10$: $\frac{4\pi}{25}(100)\frac{dh}{dt} = 10 \implies \frac{dh}{dt} = \frac{10}{16\pi} = \frac{5}{8\pi}$.
