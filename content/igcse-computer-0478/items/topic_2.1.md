# Topic 2.1 — Binary and Hexadecimal
## Items File

**Item 1 [F]**
Question: Convert the binary number 110101₂ to decimal.
Answer: 53
Difficulty: F
Topic: 2.1
Explanation: 110101₂ = 1×2⁵ + 1×2⁴ + 0×2³ + 1×2² + 0×2¹ + 1×2⁰ = 32 + 16 + 0 + 4 + 0 + 1 = 53.
Tags: binary, decimal, conversion, base-2, place values

**Item 2 [F]**
Question: Convert the decimal number 45 to binary.
Answer: 101101₂
Difficulty: F
Topic: 2.1
Explanation: Divide by 2 repeatedly, recording remainders: 45÷2=22 r1; 22÷2=11 r0; 11÷2=5 r1; 5÷2=2 r1; 2÷2=1 r0; 1÷2=0 r1. Reading remainders bottom-up: 101101₂.
Tags: decimal, binary, conversion, division method

**Item 3 [S]**
Question: Convert the hexadecimal number 2Fₕ to binary and to decimal.
Answer: Binary: 00101111₂; Decimal: 47
Difficulty: S
Topic: 2.1
Explanation: 2Fₕ = 2×16 + 15×1 = 32 + 15 = 47. For binary: each hex digit = 4 bits. 2 = 0010, F = 1111, so 2Fₕ = 00101111₂. Grouped nibble form: 0010 1111.
Tags: hexadecimal, binary, decimal, conversion, base-16

**Item 4 [S]**
Question: Explain two advantages of using hexadecimal over binary for representing memory addresses.
Answer: (1) Hexadecimal is more compact: 1 hex digit represents 4 bits, so an 8-bit byte needs only 2 hex digits. (2) Hex is easier to read and less error-prone: F3A2 is clearer than 1111001110100010. (3) Hex↔binary conversion is direct (each hex digit = 4 bits), faster than decimal↔binary.
Difficulty: S
Topic: 2.1
Explanation: Memory addresses are long binary strings. Hex reduces string length 4× while still being directly convertible to binary. This makes debugging, reading assembly code, and working with memory dumps significantly easier.
Tags: hexadecimal, memory addresses, advantages, computing practice

**Item 5 [S]**
Question: Add the binary numbers 101101₂ and 110011₂. Show all working and state if there is an overflow.
Answer: 101101₂ + 110011₂ = 1100000₂. In a 6-bit unsigned register, overflow occurs as the result requires 7 bits.
Difficulty: S
Topic: 2.1
Explanation: 101101₂ (45) + 110011₂ (51) = 1100000₂ (96). Column addition: carries propagate through all 6 positions, producing a 7th bit. In fixed-width unsigned arithmetic, this extra bit is discarded and the overflow flag is set.
Tags: binary addition, overflow, column addition, carry, unsigned arithmetic

**Item 6 [S]**
Question: Convert the binary number 11100111₂ to hexadecimal.
Answer: E7ₕ
Difficulty: S
Topic: 2.1
Explanation: Group binary into nibbles (4 bits) from the right: 11100111₂ = 1110 0111. 1110₂ = Eₕ, 0111₂ = 7ₕ. So 11100111₂ = E7ₕ.
Tags: binary, hexadecimal, conversion, nibble, grouping

**Item 7 [S]**
Question: State two methods of converting a decimal integer to binary.
Answer: (1) Division method: repeatedly divide by 2, recording remainders. Read remainders from bottom to top. (2) Subtraction method: subtract the largest powers of 2 that fit, recording a 1 for each power used and a 0 for each power skipped.
Difficulty: S
Topic: 2.1
Explanation: Division: 45÷2 → 22r1, 11r1, 5r1, 2r1, 1r0, 0r1 → 101101₂. Subtraction: largest power of 2 ≤ 45 is 32 → write 1, subtract → 13; 8 fits → 1, subtract → 5; 4 fits → 1, subtract → 1; 1 fits → 1, subtract → 0. Result: 32+8+4+1 = 101101₂.
Tags: decimal, binary, conversion methods, algorithm

**Item 8 [S]**
Question: What is the range of values representable in an unsigned 8-bit binary number?
Answer: 0 to 255 (256 distinct values)
Difficulty: S
Topic: 2.1
Explanation: Unsigned 8 bits can represent 2⁸ = 256 values. Minimum = 00000000₂ = 0. Maximum = 11111111₂ = 255.
Tags: unsigned binary, range, 8-bit, representation

**Item 9 [S]**
Question: Explain why computers use binary representation for all data.
Answer: Computers use binary because electronic circuits have two stable states: ON (current flows) and OFF (no current). Binary maps naturally to these two states (1 and 0). Circuits that detect and generate two voltages are fast, reliable, and inexpensive to manufacture compared to circuits with multiple voltage levels.
Difficulty: S
Topic: 2.1
Explanation: A circuit with 10 voltage levels to represent decimal digits would require extremely precise voltage regulation and would be much more error-prone than a simple on/off switch. Binary minimises noise sensitivity: any voltage above a threshold = 1, below = 0.
Tags: binary, electronic circuits, digital electronics, why binary

**Item 10 [F]**
Question: What is the decimal value of the binary number 1000₂?
Answer: 8
Difficulty: F
Topic: 2.1
Explanation: 1000₂ = 1×2³ + 0×2² + 0×2¹ + 0×2⁰ = 8 + 0 + 0 + 0 = 8.
Tags: binary, decimal, conversion, place values

**Item 11 [F]**
Question: Convert the hexadecimal number Aₕ to decimal.
Answer: 10
Difficulty: F
Topic: 2.1
Explanation: In hexadecimal, A = 10, B = 11, C = 12, D = 13, E = 14, F = 15. Aₕ = 10×16⁰ = 10.
Tags: hexadecimal, decimal, conversion, base-16

**Item 12 [F]**
Question: State the values represented by each bit position in an 8-bit binary number.
Answer: Bit 7 (MSB): 128, Bit 6: 64, Bit 5: 32, Bit 4: 16, Bit 3: 8, Bit 2: 4, Bit 1: 2, Bit 0 (LSB): 1.
Difficulty: F
Topic: 2.1
Explanation: Bits are numbered from right (Bit 0, least significant) to left (Bit 7, most significant). The value of each bit position n is 2ⁿ.
Tags: bit positions, place values, binary, 8-bit

**Item 13 [S]**
Question: What is the result of ANDing the binary values 11011010₂ and 10101100₂?
Answer: 10001000₂
Difficulty: S
Topic: 2.1
Explanation: Binary AND: 1 AND 1 = 1, 1 AND 0 = 0, 0 AND 1 = 0, 0 AND 0 = 0. Column by column: 1∧1=1, 1∧0=0, 0∧1=0, 1∧0=0, 1∧1=1, 0∧1=0, 1∧1=1, 0∧0=0. Result: 10001000₂.
Tags: binary AND, bitwise operations, logic gates, masks

**Item 14 [S]**
Question: Explain one use of binary AND in computing.
Answer: Binary AND is used as a bit mask to extract specific bits from a binary number. For example, to extract the most significant 4 bits of an 8-bit byte, AND it with 11110000₂ (F0ₕ). The result shows only the masked bits.
Difficulty: S
Topic: 2.1
Explanation: Masking with AND: 0 in the mask = ignore original bit (result 0); 1 in the mask = keep original bit. Used in graphics (colour channel extraction), network masks (IP address subnetting), and flag testing in programming.
Tags: bitwise AND, masking, use cases, computing applications

**Item 15 [S]**
Question: Convert the decimal number 200 to hexadecimal.
Answer: C8ₕ
Difficulty: S
Topic: 2.1
Explanation: 200 ÷ 16 = 12 remainder 8. 12 = Cₕ, 8 = 8ₕ. So 200 = C8ₕ. Check: C×16 + 8 = 192 + 8 = 200 ✓.
Tags: decimal, hexadecimal, conversion, division method

**Item 16 [C]**
Question: A pixel colour is represented as RGB(204, 51, 255). Express this in hexadecimal.
Answer: #CC33FFₕ
Difficulty: C
Topic: 2.1
Explanation: 204 ÷ 16 = 12 r12 → C; 12÷16 = 0 r12 → C. So 204 = CCₕ. 51 ÷ 16 = 3 r3 → 3; 3÷16 = 0 r3 → 3. So 51 = 33ₕ. 255 = FFₕ. Result: #CC33FFₕ.
Tags: RGB, hexadecimal, colour, conversion, HTML colour codes

**Item 17 [C]**
Question: Explain the difference between binary addition and binary AND, and give one use of each.
Answer: Binary addition (OR): 0+0=0, 0+1=1, 1+0=1, 1+1=10 (carry 1). Binary AND: 0∧0=0, 0∧1=0, 1∧0=0, 1∧1=1. Use of addition: arithmetic in CPU ALU to compute sums. Use of AND: bit masking to extract specific bits (e.g., subnet masking in networking).
Difficulty: C
Topic: 2.1
Explanation: Binary addition is column-by-column with carries — it is arithmetic. Binary AND operates on each bit independently — it is a logical operation. The truth tables differ: 1+1=10 in addition vs 1∧1=1 in AND.
Tags: binary addition, binary AND, difference, uses, truth table

**Item 18 [C]**
Question: In a 4-bit two's complement system, represent the decimal number −3 and explain how negative numbers are stored.
Answer: −3 in two's complement = 1101₂. To form two's complement negative: invert bits of +3 (0011 → 1100) then add 1 (1100 + 0001 = 1101). MSB = 1 indicates negative. Range: −8 to +7.
Difficulty: C
Topic: 2.1
Explanation: Two's complement stores negative numbers by inverting all bits of the positive value and adding 1. This means only one representation of zero (0000) and an asymmetric range (most negative is −2ⁿ⁻¹). The MSB is the sign bit. 1101₂ = −8+4+0+1 = −3 ✓.
Tags: two's complement, negative numbers, signed binary, representation
