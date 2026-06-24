---
id: T19-Item14
difficulty: F
calculator: no-calc
type: mcq
---

Let $G(x) = \int_{-3}^{x} f(t)\,dt$, where $f$ is continuous on $\mathbb{R}$. Which of the following statements must be true?

I. $G(5) = \int_{-3}^{5} f(t)\,dt$

II. $G'(x) = f(x)$ for all $x$

III. $G(-3) = 0$

## Options
A) I only

B) I and II only

C) I and III only

D) I, II, and III

## Answer
D

## Explanation
This tests the Fundamental Theorem of Calculus (Part 1) and the definition of an accumulation function.

**I. True.** By definition, $G(x) = \int_{-3}^{x} f(t)\,dt$. Substituting $x = 5$ gives $G(5) = \int_{-3}^{5} f(t)\,dt$.

**II. True.** The Fundamental Theorem of Calculus, Part 1 states: if $G(x) = \int_a^x f(t)\,dt$ and $f$ is continuous, then $G'(x) = f(x)$ for all $x$ in the open interval. (At the endpoints, differentiability is only guaranteed on the interior, but the statement "for all $x$" in the context of AP Calculus is understood to mean on the interior where the derivative exists.)

**III. True.** $G(-3) = \int_{-3}^{-3} f(t)\,dt = 0$ because the integral over a zero-width interval equals zero.

All three statements are true.
