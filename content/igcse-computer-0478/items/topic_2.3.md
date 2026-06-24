# Topic 2.3 — Floating-point Numbers
## Items File

**Item 1 [F]**
Question: What does floating-point representation allow computers to store?
Answer: Very large and very small real numbers (numbers with a fractional part) beyond the range of integers.
Difficulty: F
Topic: 2.3
Explanation: Integer arithmetic cannot represent 3.14, −0.000001, or 1,000,000,000. Floating-point uses scientific notation in binary to represent a much wider range of values.
Tags: floating-point, real numbers, representation, range

**Item 2 [F]**
Question: What are the two main components of a floating-point number?
Answer: (1) Significand (or mantissa) — the significant digits of the number. (2) Exponent — the power by which the base is raised.
Difficulty: F
Topic: 2.3
Explanation: In decimal: 3.14 × 10², the significand is 3.14 and the exponent is 2. Binary follows the same principle with base 2.
Tags: floating-point, significand, mantissa, exponent

**Item 3 [F]**
Question: What is normalised floating-point representation?
Answer: A number is normalised when the significand has no leading zeros — the first digit after the binary point is 1.
Difficulty: F
Topic: 2.3
Explanation: In binary: 1.0101 × 2³ is normalised. 0.0101 × 2⁴ is not normalised (has leading zeros). Normalisation maximises precision.
Tags: normalisation, floating-point, binary point, precision

**Item 4 [F]**
Question: Convert the decimal number 5.75 to binary floating-point form (normalised).
Answer: 5.75 = 101.11₂ = 1.0111 × 2²
Difficulty: F
Topic: 2.3
Explanation: 5 = 101₂. 0.75 = 0.5 + 0.25 = 0.11₂. So 5.75 = 101.11₂. Shift binary point left 2 places to normalise: 1.0111 × 2².
Tags: floating-point, binary, normalisation, conversion

**Item 5 [S]**
Question: Explain the purpose of the exponent in floating-point representation.
Answer: The exponent shifts the binary point, allowing the same significand to represent vastly different magnitudes (very large or very small numbers).
Difficulty: S
Topic: 2.3
Explanation: The significand determines precision; the exponent determines magnitude. Without an exponent, only numbers approximately between 1 and 2 could be represented.
Tags: exponent, floating-point, magnitude, range

**Item 6 [S]**
Question: What is the effect of increasing the number of bits in the exponent field?
Answer: The range of representable numbers increases (largest and smallest values grow), but precision decreases because fewer bits remain for the significand.
Difficulty: S
Topic: 2.3
Explanation: Range and precision are traded off. A larger exponent gives a wider range but coarser steps between consecutive representable numbers.
Tags: exponent bits, range, precision, trade-off

**Item 7 [S]**
Question: What is normalised form for a negative floating-point number?
Answer: The sign bit = 1. The significand has no leading zeros after the binary point (same rule as positive), and the exponent adjusts accordingly.
Difficulty: S
Topic: 2.3
Explanation: −5.75 = −1.0111 × 2². Sign bit = 1 (negative), normalised significand = 1.0111, exponent = 2.
Tags: negative floating-point, normalisation, sign bit

**Item 8 [S]**
Question: State one problem that can occur when performing arithmetic on floating-point numbers.
Answer: Rounding error — because only a fixed number of bits are available for the significand, the result of an operation may need to be rounded to the nearest representable value.
Difficulty: S
Topic: 2.3
Explanation: Not all real numbers can be exactly represented in binary floating-point. For example, 0.1 in decimal has an infinitely recurring binary representation, so it is rounded.
Tags: rounding error, floating-point arithmetic, precision loss

**Item 9 [S]**
Question: Why can 0.1 + 0.2 ≠ 0.3 in floating-point arithmetic?
Answer: Because 0.1 and 0.2 cannot be represented exactly in binary floating-point — both are approximated. The approximations accumulate, producing a result that differs from the exact 0.3.
Difficulty: S
Topic: 2.3
Explanation: 0.1₁₀ = 0.0001100110011...₂ (repeating). When stored in 32-bit or 64-bit floating-point, it is rounded. The errors in 0.1 + 0.2 differ from the error in 0.3.
Tags: floating-point, rounding, precision, binary representation

**Item 10 [S]**
Question: What is a normalised mantissa in the context of IEEE 754?
Answer: A normalised mantissa has an implicit leading 1 bit (for single precision), meaning it is always in the form 1.xxxx, maximising precision.
Difficulty: S
Topic: 2.3
Explanation: IEEE 754 does not store the leading 1 explicitly — it is implicit. This gives 24 bits of precision (1 implicit + 23 stored) in single precision.
Tags: IEEE 754, normalised mantissa, implicit 1, precision

**Item 11 [S]**
Question: Explain why floating-point normalisation is important.
Answer: Normalisation ensures the maximum number of significant digits are stored, reducing wasted leading zeros and increasing precision.
Difficulty: S
Topic: 2.3
Explanation: Without normalisation, 0.00101 × 2³ and 1.01 × 2⁰ represent the same number but use different significand bits. Normalisation eliminates ambiguity and uses all bits efficiently.
Tags: normalisation, precision, floating-point, significance

**Item 12 [S]**
Question: What is overflow in the context of floating-point numbers?
Answer: Overflow occurs when a number is too large (positive or negative) to be represented in the given floating-point format, even with the maximum exponent.
Difficulty: S
Topic: 2.3
Explanation: In IEEE single precision, the largest normalised number ≈ 3.4 × 10³⁸. Anything beyond this overflows, typically producing +∞ or −∞.
Tags: overflow, floating-point, maximum value, exponent

**Item 13 [C]**
Question: Represent the decimal number 0.375 in IEEE 754 single precision normalised form and show the binary scientific notation.
Answer: 0.375₁₀ = 0.011₂ = 1.1 × 2⁻²
Difficulty: C
Topic: 2.3
Explanation: 0.375 = 1/4 + 1/8 = 0.011₂. To normalise: shift binary point right 2 places → 1.1 × 2⁻². The exponent is −2. Sign bit = 0.
Tags: floating-point, IEEE 754, normalisation, small numbers

**Item 14 [C]**
Question: In IEEE 754 single precision, what is the effect of a bias of 127 on the exponent field?
Answer: The bias shifts all exponents by +127 so that negative exponents (for small numbers) can be stored as positive binary values. An exponent of −1 is stored as 126.
Difficulty: C
Topic: 2.3
Explanation: Stored exponent = actual exponent + bias. Range of stored exponent: 1 to 254 (0 and 255 reserved). Actual exponent range: −126 to +127.
Tags: exponent bias, IEEE 754, stored exponent, single precision

**Item 15 [C]**
Question: What is underflow in floating-point arithmetic?
Answer: Underflow occurs when a non-zero number is too small in magnitude to be represented — it is between the smallest normalised number and zero.
Difficulty: C
Topic: 2.3
Explanation: In IEEE 754, the smallest positive normalised number ≈ 1.2 × 10⁻³⁸. Numbers smaller than this but greater than zero may be flushed to zero (gradual underflow) or produce a denormal number.
Tags: underflow, floating-point, denormal, smallest number

**Item 16 [C]**
Question: Compare fixed-point and floating-point representation in terms of precision.
Answer: Fixed-point has uniform precision across its range — the spacing between consecutive values is constant. Floating-point has uniform relative precision — the spacing grows proportionally with the magnitude.
Difficulty: C
Topic: 2.3
Explanation: Fixed-point (e.g., 8.8 format): 0.001 and 1000.001 differ by the same representable step. Floating-point: relative precision is constant (~24 bits), so absolute precision degrades at large magnitudes.
Tags: fixed-point, floating-point, precision comparison, absolute vs relative

**Item 17 [C]**
Question: Explain what a denormal (subnormal) number is in IEEE 754.
Answer: A denormal number has an exponent of 0 and does not use the implicit leading 1 bit. It allows representtion of numbers smaller than the smallest normalised number at the cost of reduced precision.
Difficulty: C
Topic: 2.3
Explanation: Denormals fill the gap between the smallest normalised number and zero. They use the full range of the significand bits but sacrifice leading-digit precision.
Tags: denormal, subnormal, IEEE 754, precision, underflow

**Item 18 [C]**
Question: In IEEE 754 single precision, how many bits are allocated to each field, and what are their purposes?
Answer: 1 bit (sign) + 8 bits (exponent) + 23 bits (fraction/mantissa) = 32 bits total. The sign bit determines positive/negative. The biased exponent determines magnitude. The fraction stores the precision bits.
Difficulty: C
Topic: 2.3
Explanation: Exponent bias = 127. With the implicit 1, effective precision = 24 bits (about 7 decimal digits). Range ≈ ±3.4 × 10³⁸. Smallest positive ≈ 1.2 × 10⁻³⁸.
Tags: IEEE 754, single precision, bit layout, exponent, mantissa
