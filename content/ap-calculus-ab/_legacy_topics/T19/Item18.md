---
id: T19-Item18
difficulty: C
calculator: calc
type: frq
---

A car moves along a straight road. The velocity $v(t)$ of the car, in meters per second, is given by $v(t) = 30t - t^2$ for $0 \leq t \leq 30$, where $t$ is measured in seconds.

**(a)** Using a left Riemann sum with $n = 5$ subintervals, approximate the total distance traveled by the car over the interval $0 \leq t \leq 30$. Show your setup and calculation.

**(b)** Using a right Riemann sum with $n = 5$ subintervals, approximate the total distance traveled. Show your calculation.

**(c)** Using the trapezoidal rule with $n = 5$ subintervals, approximate $\int_0^{30} v(t)\,dt$.

**(d)** Find the exact value of $\int_0^{30} v(t)\,dt$ using an antiderivative.

**(e)** Which of the approximations from parts (a), (b), and (c) is closest to the exact value? Calculate the percent error for each.

---

## Answer

**(a)** Left Riemann sum with $n = 5$ on $[0, 30]$:
$$\Delta t = \frac{30 - 0}{5} = 6$$

Left endpoints: $t = 0, 6, 12, 18, 24$

$$L_5 = 6[v(0) + v(6) + v(12) + v(18) + v(24)]$$
$$v(0) = 0, \; v(6) = 180 - 36 = 144, \; v(12) = 360 - 144 = 216, \; v(18) = 540 - 324 = 216, \; v(24) = 720 - 576 = 144$$
$$L_5 = 6[0 + 144 + 216 + 216 + 144] = 6(720) = 4320 \text{ m}$$

**(b)** Right Riemann sum with $n = 5$:
Right endpoints: $t = 6, 12, 18, 24, 30$

$$R_5 = 6[v(6) + v(12) + v(18) + v(24) + v(30)]$$
$$v(30) = 900 - 900 = 0$$
$$R_5 = 6[144 + 216 + 216 + 144 + 0] = 6(720) = 4320 \text{ m}$$

Since $v(t)$ is symmetric about $t = 15$, we get $L_5 = R_5$ in this case.

**(c)** Trapezoidal rule with $n = 5$:
$$T_5 = \frac{6}{2}[v(0) + 2v(6) + 2v(12) + 2v(18) + 2v(24) + v(30)]$$
$$= 3[0 + 2(144) + 2(216) + 2(216) + 2(144) + 0]$$
$$= 3[0 + 288 + 432 + 432 + 288 + 0] = 3(1440) = 4320 \text{ m}$$

**(d)** Exact integral:
$$\int_0^{30} (30t - t^2)\,dt = \left[15t^2 - \frac{t^3}{3}\right]_0^{30}$$
$$= 15(900) - \frac{27000}{3} = 13500 - 9000 = 4500 \text{ m}$$

**(e)** Percent errors:
- Left sum: $\left|\frac{4320 - 4500}{4500}\right| \times 100\% = 4\%$
- Right sum: $4\%$
- Trapezoidal: $4\%$

All three approximations give the same value for this symmetric velocity function, each with a 4% error relative to the exact value.
