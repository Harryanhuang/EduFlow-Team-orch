# Topic 1.1 — Number Systems and Binary Representation
## Items File

**Item 1 [F]**
Question: Convert the binary number 10110₂ to decimal.
Answer: 22
Difficulty: F
Topic: 1.1
Explanation: 10110₂ = 1×2⁴ + 0×2³ + 1×2² + 1×2¹ + 0×2⁰ = 16 + 0 + 4 + 2 + 0 = 22.
Tags: binary, decimal, conversion, base-2

**Item 2 [F]**
Question: Convert the decimal number 37 to binary using the division method.
Answer: 100101₂
Difficulty: F
Topic: 1.1
Explanation: 37÷2=18 r1; 18÷2=9 r0; 9÷2=4 r1; 4÷2=2 r0; 2÷2=1 r0; 1÷2=0 r1. Reading bottom-up: 100101₂. Check: 32+4+1=37 ✓.
Tags: decimal, binary, division method, conversion

**Item 3 [F]**
Question: What is the hexadecimal representation of the decimal number 255?
Answer: FFₕ
Difficulty: F
Topic: 1.1
Explanation: 255 ÷ 16 = 15 remainder 15. 15 = Fₕ. Reading: FFₕ. Check: FFₕ = 15×16 + 15 = 240 + 15 = 255 ✓.
Tags: hexadecimal, decimal, conversion, FFₕ

**Item 4 [S]**
Question: Explain why hexadecimal is commonly used in computing.
Answer: Hexadecimal is used because it is easier for humans to read and write than binary. 1 hex digit represents 4 binary bits, so memory addresses and colour codes are much shorter in hex. Conversion between hex and binary is direct (each hex digit = 4 bits).
Difficulty: S
Topic: 1.1
Explanation: A 32-bit memory address in binary has 32 digits; in hex it has only 8 digits. This reduces human error and makes debugging significantly easier.
Tags: hexadecimal, computing, representation, advantages

**Item 5 [S]**
Question: Add the binary numbers 1101₂ and 1011₂. Show your working.
Answer: 11000₂
Difficulty: S
Topic: 1.1
Explanation: 1101₂ + 1011₂ = 11000₂. Column addition: 1+1=0 carry 1; 0+1+carry1=0 carry 1; 1+0+carry1=0 carry 1; 1+1+carry1=1 carry 1; carry 1 out. Result: 11000₂ = 24.
Tags: binary addition, column method, carry, overflow

**Item 6 [S]**
Question: Convert the binary number 11110000₂ to hexadecimal.
Answer: F0ₕ
Difficulty: S
Topic: 1.1
Explanation: Group into nibbles from right: 1111 0000. 1111₂ = Fₕ (15), 0000₂ = 0ₕ. Result: F0ₕ. Check: F0ₕ = 240, 11110000₂ = 240 ✓.
Tags: binary, hexadecimal, nibble, conversion

**Item 7 [S]**
Question: State the number of distinct values representable in an n-bit binary number.
Answer: 2ⁿ distinct values
Difficulty: S
Topic: 1.1
Explanation: Each bit doubles the number of representable values. An n-bit binary number can represent 2ⁿ distinct values. For example: 8 bits = 2⁸ = 256 values (0 to 255).
Tags: binary, number of values, bits, representation

**Item 8 [S]**
Question: Convert the hexadecimal number 3Aₕ to decimal.
Answer: 58
Difficulty: S
Topic: 1.1
Explanation: 3Aₕ = 3×16 + 10 = 48 + 10 = 58. Check: 3Aₕ = 0011 1010₂ = 58 ✓.
Tags: hexadecimal, decimal, conversion

**Item 9 [S]**
Question: What is the binary and hexadecimal representation of the decimal number 16?
Answer: Binary: 10000₂; Hexadecimal: 10ₕ
Difficulty: S
Topic: 1.1
Explanation: 16 = 2⁴ = 10000₂. In hex, 16 = 1×16¹ + 0 = 10ₕ. 10ₕ is significant because it is the base (hex 10 = decimal 16).
Tags: decimal, binary, hexadecimal, conversion, base

**Item 10 [F]**
Question: What is the maximum decimal value of a 4-bit binary number?
Answer: 15
Difficulty: F
Topic: 1.1
Explanation: 4 bits = 2⁴ = 16 values (0 to 15). Maximum = 1111₂ = 15.
Tags: binary, maximum value, range, 4-bit

**Item 11 [F]**
Question: State two advantages of storing numbers in binary over decimal in a computer.
Answer: (1) Binary maps directly to two voltage states (on/off), making circuits simpler and more reliable. (2) Binary arithmetic is easier to implement in hardware using logic gates.
Difficulty: F
Topic: 1.1
Explanation: Binary circuits are noise-resistant because any voltage above/below a threshold reads as 1/0. Decimal would require precise voltage discrimination between 10 levels.
Tags: binary, advantages, electronic circuits

**Item 12 [F]**
Question: Convert the binary number 10000000₂ to decimal.
Answer: 128
Difficulty: F
Topic: 1.1
Explanation: 10000000₂ = 1×2⁷ = 128. In hexadecimal: 80ₕ.
Tags: binary, decimal, conversion, powers of 2

**Item 13 [S]**
Question: Subtract 101₂ from 1100₂ using binary subtraction with borrowing.
Answer: 111₂
Difficulty: S
Topic: 1.1
Explanation: 1100₂ − 0101₂ = 0111₂. Working right to left: 0−1: borrow → 2−1=1, borrow from next column. Next column: 0 (after borrow) − 0 = 0. Next: 1−1=0. Result: 0111₂. Check: 1100₂=12, 0101₂=5, 12−5=7=111₂ ✓.
Tags: binary subtraction, borrowing, two's complement method

**Item 14 [S]**
Question: Explain why a kilobyte is 1024 bytes and not 1000 bytes.
Answer: Computers use binary (base 2), not decimal. 1 KiB = 2¹⁰ = 1024 bytes. 1 KB (decimal) = 1000 bytes. The prefixes k/M/G retain their computing meaning (powers of 2) or decimal meaning (powers of 10) depending on context.
Difficulty: S
Topic: 1.1
Explanation: 2¹⁰ = 1024. Binary prefixes (KiB, MiB) distinguish from decimal (KB, MB = 1000 bytes). Binary and decimal meanings diverge as sizes grow: MiB = 1,048,576 bytes; MB = 1,000,000 bytes.
Tags: kilobyte, binary prefix, units, 1024

**Item 15 [S]**
Question: Convert 1.5 gigabytes (decimal) to megabytes and kilobytes.
Answer: 1.5 GB = 1500 MB = 1,500,000 KB
Difficulty: S
Topic: 1.1
Explanation: Decimal prefixes: G = 10⁹, M = 10⁶, K = 10³. 1.5 GB = 1.5 × 10⁹ bytes = 1,500,000,000 bytes = 1,500 MB = 1,500,000 KB. In binary: 1.5 GiB = 1.5 × 2³⁰ = 1,610,612,736 bytes.
Tags: decimal prefixes, gigabyte, megabyte, unit conversion

**Item 16 [C]**
Question: In an 8-bit two's complement system, represent −42 and explain the result.
Answer: −42 in 8-bit two's complement = 11010110₂.
Difficulty: C
Topic: 1.1
Explanation: To find −42 in two's complement: (1) +42 = 00101010₂. (2) Invert all bits: 11010101. (3) Add 1: 11010110. This is the 8-bit representation. Verification: invert 11010110 → 00101001; add 1 → 00101010₂ = 42 ✓. The MSB = 1 indicates a negative value. Bit-by-bit: −128 + 64 + 16 + 4 + 2 = −42 ✓.
Tags: two's complement, signed binary, negative numbers, 8-bit, representation

**Item 17 [C]**
Question: Explain why two's complement representation is preferred over sign-and-magnitude for storing negative integers.
Answer: Two's complement has one representation of zero (00000000), uses the full range (−128 to +127 for 8-bit), and simplifies arithmetic circuits — the same adder circuit handles addition and subtraction. Sign-and-magnitude has two zeros (+0 and −0) and complicates comparison and arithmetic.
Difficulty: C
Topic: 1.1
Explanation: In sign-and-magnitude, −42 = 10101010, with MSB = 1. Two's complement gives one zero and arithmetic works naturally with a single adder circuit (subtraction is addition of the two's complement). Most CPUs use two's complement for signed integers.
Tags: two's complement, sign-and-magnitude, representation, advantages

**Item 18 [C]**
Question: In a 5-bit two's complement system, list all representable values and identify the range.
Answer: Range: −16 to +15. Minimum: 10000₂ = −16. Maximum: 01111₂ = +15.
Difficulty: C
Topic: 1.1
Explanation: For n bits in two's complement: minimum = −2ⁿ⁻¹ = −2⁴ = −16. Maximum = 2ⁿ⁻¹ − 1 = 2⁴−1 = 15. The MSB (bit 4) is the sign bit, contributing −16 when 1. The most negative value has no positive equivalent in two's complement.
Tags: two's complement, range, 5-bit, minimum, maximum
