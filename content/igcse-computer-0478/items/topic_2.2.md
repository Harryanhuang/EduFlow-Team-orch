# Topic 2.2 — Two's Complement
## Items File

**Item 1 [F]**
Question: What is the range of values representable in a 4-bit two's complement system?
Answer: −8 to +7
Difficulty: F
Topic: 2.2
Explanation: For n bits in two's complement: minimum = −2ⁿ⁻¹ = −2³ = −8. Maximum = 2ⁿ⁻¹ − 1 = 2³ − 1 = 7.
Tags: two's complement, range, 4-bit, signed numbers

**Item 2 [F]**
Question: Convert the binary number 0111₂ to decimal, assuming two's complement representation.
Answer: +7
Difficulty: F
Topic: 2.2
Explanation: MSB (leftmost bit) = 0, so the number is positive. 0111₂ = 4+2+1 = 7. In two's complement, 0 as MSB means positive.
Tags: two's complement, binary, decimal, positive number

**Item 3 [F]**
Question: What does the most significant bit (MSB) represent in two's complement?
Answer: The sign bit. MSB = 0 means the number is positive. MSB = 1 means the number is negative.
Difficulty: F
Topic: 2.2
Explanation: In two's complement, the MSB carries a negative place value. For n bits, MSB contributes −2ⁿ⁻¹ rather than +2ⁿ⁻¹.
Tags: MSB, sign bit, two's complement, signed binary

**Item 4 [F]**
Question: Convert the decimal number −3 to an 8-bit two's complement binary number.
Answer: 11111101₂
Difficulty: F
Topic: 2.2
Explanation: Method: (1) Write +3 = 00000011₂. (2) Invert all bits: 11111100. (3) Add 1: 11111101. Result: 11111101₂ = −3 in two's complement. Verify: invert 11111101 → 00000010; add 1 → 00000011 = 3 ✓.
Tags: two's complement, negative numbers, conversion, 8-bit

**Item 5 [S]**
Question: Explain why two's complement is used to represent negative integers in computers.
Answer: Two's complement has a single representation for zero, uses the full range of values, and simplifies hardware — the same adder circuit handles both addition and subtraction.
Difficulty: S
Topic: 2.2
Explanation: Sign-and-magnitude has two zeros (+0 and −0), complicating comparisons. Ones' complement also has two zeros. Two's complement's single zero and natural arithmetic make it the standard.
Tags: two's complement, advantages, hardware, binary representation

**Item 6 [S]**
Question: Convert the binary number 10010100₂ to decimal, assuming 8-bit two's complement.
Answer: −108
Difficulty: S
Topic: 2.2
Explanation: MSB = 1, so negative. Bit values from MSB (bit 7) to LSB (bit 0): 1(−128) + 0(64) + 0(32) + 1(16) + 0(8) + 1(4) + 0(2) + 0(1) = −128 + 16 + 4 = −108. Verified by two's complement: invert 10010100 → 01101011; add 1 → 01101100₂ = 108 ✓.
Tags: two's complement, binary to decimal, negative, MSB

**Item 7 [S]**
Question: What is the two's complement of 00000000₂? Give the result and its meaning.
Answer: 00000000₂. The two's complement of zero is zero itself (there is only one representation for zero).
Difficulty: S
Topic: 2.2
Explanation: Invert: 11111111. Add 1: 1 00000000. Drop the carry bit (overflow beyond 8 bits): 00000000. This is a key advantage over sign-and-magnitude.
Tags: two's complement, zero, overflow, 8-bit

**Item 8 [S]**
Question: In an 8-bit two's complement system, what is the decimal value of 10000000₂?
Answer: −128
Difficulty: S
Topic: 2.2
Explanation: MSB = 1, so negative. Value = −128 + 0 = −128. This is the most negative representable value in 8-bit two's complement.
Tags: two's complement, minimum value, MSB, 8-bit

**Item 9 [S]**
Question: Subtract 00101011₂ from 01000000₂ using two's complement addition.
Answer: 00010101₂ = 21
Difficulty: S
Topic: 2.2
Explanation: To subtract, add the two's complement of the subtrahend. Two's complement of 00101011: invert → 11010100; add 1 → 11010101. Add: 01000000 + 11010101 = 1 00010101. Drop the carry (9th bit): 00010101₂ = 21. Check: 64 − 43 = 21 ✓.
Tags: two's complement, subtraction, binary addition, overflow

**Item 10 [S]**
Question: What happens when 127 (01111111₂) and 1 are added in 8-bit two's complement? State the result.
Answer: The result wraps around to −128 (10000000₂). This is overflow — the correct answer (+128) cannot be represented.
Difficulty: S
Topic: 2.2
Explanation: 01111111 + 00000001 = 10000000. MSB = 1 means negative, but the correct result +128 is beyond the representable range (−128 to +127). This is arithmetic overflow.
Tags: overflow, two's complement, addition, 8-bit range

**Item 11 [S]**
Question: Convert −1 to a 4-bit two's complement binary number.
Answer: 1111₂
Difficulty: S
Topic: 2.2
Explanation: +1 = 0001. Invert: 1110. Add 1: 1111. Result: 1111₂ = −1. Verify: invert 1111 → 0000; add 1 → 0001 = 1 ✓. In n-bit two's complement, −1 is always all 1 bits.
Tags: two's complement, −1, 4-bit, binary representation

**Item 12 [S]**
Question: Explain why 10000000₂ is −128 in 8-bit two's complement, not −0.
Answer: Because the MSB carries a place value of −128, not −0. Any bit pattern with MSB = 1 is negative, with value = −128 plus the positive contributions of remaining bits.
Difficulty: S
Topic: 2.2
Explanation: In sign-and-magnitude, 10000000 would be −0. In two's complement, 10000000 has no positive bits: −128 + 0 = −128. The most negative value has no positive equivalent.
Tags: two's complement, MSB, −128, signed representation

**Item 13 [C]**
Question: In a 4-bit two's complement system, perform the subtraction 3 − 5 and show the result.
Answer: 3 − 5 = −2, represented as 1110₂ in two's complement.
Difficulty: C
Topic: 2.2
Explanation: Convert 5 to −5 in two's complement: +5 = 0101, invert → 1010, add 1 → 1011. Add: 0011 + 1011 = 1110. MSB = 1 → negative. Verify: invert 1110 → 0001; add 1 → 0010 = 2 ✓. Result = −2.
Tags: two's complement, subtraction, negative result, 4-bit

**Item 14 [C]**
Question: What is the result of adding 11010100₂ and 00101100₂ in 8-bit two's complement? State whether overflow occurred.
Answer: Result: 00000000₂ = 0. No overflow occurred.
Difficulty: C
Topic: 2.2
Explanation: Binary addition: 11010100 + 00101100 = 1 00000000. The 9th carry bit (overflow) is discarded, leaving 00000000. MSB of result = 0 (positive), correct range. No overflow flag set because both operands had MSB = 1 (both negative) or both had MSB = 0 (both positive).
Tags: two's complement, addition, overflow detection, 8-bit

**Item 15 [C]**
Question: Explain how to detect arithmetic overflow in two's complement addition. Apply your method to 01111111 + 01000000.
Answer: Overflow is detected when the carry into the MSB differs from the carry out of the MSB. For 01111111 + 01000000: carry into MSB = 1 (from bit 6), carry out = 0. Overflow occurred — correct answer should be +126 but result is −2.
Difficulty: C
Topic: 2.2
Explanation: 01111111 (127) + 01000000 (64) = 10111111 (−65 in two's complement). The correct result +191 is outside the range. Overflow detection: bit 6 → bit 7 carry = 1; carry out of bit 7 = 0. 1 ≠ 0 → overflow.
Tags: overflow detection, carry method, two's complement addition, range error

**Item 16 [C]**
Question: A computer uses 8-bit two's complement. A program stores the value −50. Show the binary representation and verify it by converting back to decimal.
Answer: −50 in 8-bit two's complement = 11001110₂.
Difficulty: C
Topic: 2.2
Explanation: +50 = 00110010. Invert: 11001101. Add 1: 11001110. Verify: MSB=1 → negative. Value = −128 + 64+0+0+8+4+2+0 = −128+78 = −50 ✓.
Tags: two's complement, negative conversion, verification, 8-bit

**Item 17 [C]**
Question: Compare the range of unsigned 8-bit integers with the range of signed 8-bit two's complement integers.
Answer: Unsigned: 0 to 255 (256 values). Two's complement signed: −128 to +127 (256 values). Both represent 256 distinct values but distribute them differently.
Difficulty: C
Topic: 2.2
Explanation: Unsigned uses all 8 bits for magnitude: 2⁸ = 256 values (0–255). Two's complement uses MSB as −2⁷ = −128, giving range −128 to +127. The total count is identical.
Tags: unsigned, signed, range comparison, two's complement, 8-bit

**Item 18 [C]**
Question: In an 8-bit two's complement system, adding 11111111₂ and 00000001₂ gives 00000000. Is this overflow? Explain.
Answer: No overflow occurred. Both operands have MSB = 1 (negative) and MSB = 0 (positive) respectively — one positive, one negative. Overflow only occurs when both operands have the same sign and the result has a different sign.
Difficulty: C
Topic: 2.2
Explanation: 11111111₂ = −1, 00000001₂ = +1. Sum = 0. Correct result is 0, which is representable. Overflow detection rule: if both addends are negative (MSB=1) and result MSB=0, overflow. If both addends are positive (MSB=0) and result MSB=1, overflow. Here, signs differ → no overflow.
Tags: overflow, two's complement, addition, overflow detection rule
