---
id: T23-Item16
difficulty: C
calculator: calc
type: frq
---
A savings account with initial balance $B(0) = \$1000$ earns interest at a rate of 5% per year, compounded continuously. At the same time, money is withdrawn from the account at a rate of $W$ dollars per year.

**(a)** Write a differential equation for $B(t)$, the balance after $t$ years.

**(b)** If $W = \$30$ per year, find the balance function $B(t)$.

**(c)** What is the largest withdrawal rate $W$ that allows the account to grow indefinitely without depleting?

**(d)** With $W = \$30$, how long until the balance reaches \$2000?

## Answer
**(a)** The continuous interest adds $0.05B$ per year, while withdrawals subtract $W$:
$$\dfrac{dB}{dt} = 0.05B - W$$

**(b)** This is a linear differential equation:
$$\dfrac{dB}{dt} - 0.05B = -30$$

Integrating factor: $\mu(t) = e^{-0.05t}$

$$(Be^{-0.05t})' = -30e^{-0.05t}$$
$$Be^{-0.05t} = 600e^{-0.05t} + C$$

Using $B(0) = 1000$:
$$1000 = 600 + C \implies C = 400$$

$$B(t) = 600 + 400e^{0.05t}$$

**(c)** For the account to grow indefinitely (never deplete), we need $dB/dt > 0$ for all time. The equilibrium is $B^* = W/0.05 = 20W$. Since $B$ approaches equilibrium from below when $W < 50$ and from above when $W > 50$, the critical value is $W_c = 0.05 \times 1000 = 50$ dollars per year. For $W < 50$, the balance grows toward infinity; for $W \geq 50$, the balance eventually depletes or stagnates.

**(d)** Set $B(t) = 2000$:
$$2000 = 600 + 400e^{0.05t}$$
$$1400 = 400e^{0.05t}$$
$$e^{0.05t} = 3.5$$
$$t = \dfrac{\ln 3.5}{0.05} = 20\ln 3.5 \approx 25.1 \text{ years}$$

## Explanation
This problem combines exponential growth with a constant drain, a common financial modeling scenario. The equilibrium $B = W/0.05$ represents the steady-state balance that the account approaches. The critical withdrawal rate is 5% of the balance, which makes sense: earning 5% per year, any withdrawal less than this allows eventual growth.
