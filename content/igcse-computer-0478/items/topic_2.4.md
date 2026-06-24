# Topic 2.4 — Hexadecimal Representation
## Items File

**Item 1 [F]**
Question: Convert the hexadecimal digit D to decimal.
Answer: D represents 13 in decimal.
Difficulty: F
Topic: 2.4
Explanation: In hexadecimal, digits range from 0 to 9, then A (10), B (11), C (12), D (13), E (14), and F (15). Memorising these values is essential for conversion.
Tags: hexadecimal, conversion, decimal

**Item 2 [F]**
Question: What is the main reason hexadecimal is used in computing instead of decimal?
Answer: Hexadecimal converts very easily from and to binary, since each hex digit represents exactly 4 binary bits. It is a much shorter and more readable notation for long binary numbers.
Difficulty: F
Topic: 2.4
Explanation: A single hex digit covers 4 binary bits, so an 8-bit byte is represented by exactly 2 hex digits. This makes hex ideal for representing byte values.
Tags: hexadecimal, binary, advantages

**Item 3 [F]**
Question: Convert the binary number 1101 to hexadecimal.
Answer: 1101 = D in hexadecimal.
Difficulty: F
Topic: 2.4
Explanation: Group the binary digits into sets of 4 from the right. 1101 is already 4 bits, which equals D (13) in hex.
Tags: hexadecimal, binary conversion

**Item 4 [F]**
Question: What is the hexadecimal representation of the decimal number 15?
Answer: F.
Difficulty: F
Topic: 2.4
Explanation: Decimal 15 corresponds to binary 1111, which is F in hexadecimal. This is the maximum value for a single hex digit.
Tags: hexadecimal, decimal conversion

**Item 5 [F]**
Question: Convert the hexadecimal number 1A to decimal.
Answer: 1A = 26 in decimal (1 × 16 + 10 = 26).
Difficulty: F
Topic: 2.4
Explanation: Each hex digit is multiplied by its place value (16^0, 16^1, 16^2, and so on). Here, 1 is in the 16s place and A (10) is in the 1s place.
Tags: hexadecimal, decimal conversion

**Item 6 [F]**
Question: Why is memory address 00FF often written in hexadecimal rather than binary?
Answer: As 00FF, it is much shorter and easier to read than the binary equivalent 0000000011111111. Hexadecimal reduces the chance of errors when reading or writing addresses.
Difficulty: F
Topic: 2.4
Explanation: Binary representations of memory addresses are long and error-prone. A 32-bit address is 32 digits in binary but only 8 digits in hex.
Tags: hexadecimal, memory addresses, advantages

**Item 7 [S]**
Question: Convert the binary number 10110011 to hexadecimal.
Answer: 10110011 = B3 in hexadecimal.
Difficulty: S
Topic: 2.4
Explanation: Split into two groups of 4: 1011 = B and 0011 = 3. Therefore the hex value is B3.
Tags: hexadecimal, binary conversion

**Item 8 [S]**
Question: Add the hexadecimal numbers 1F and 2A.
Answer: 1F + 2A = 49 (1F = 31, 2A = 42, 31 + 42 = 73 = 49 in hex).
Difficulty: S
Topic: 2.4
Explanation: Convert each to decimal, add, then convert back to hex. Alternatively, add digit by digit with carries where needed: F + A = 15 + 10 = 25 = 19 with carry 1; then 1 + 2 + 1 = 4.
Tags: hexadecimal, hex arithmetic

**Item 9 [S]**
Question: The colour code #FF0000 represents red in web colour notation. Explain what this means in binary.
Answer: FF = 11111111 for red, and 00 = 00000000 for both green and blue. Each pair of hex digits represents 8 bits, giving maximum red intensity and zero green and blue.
Difficulty: S
Topic: 2.4
Explanation: Web colours use RGB notation where each component ranges from 00 to FF. FF means all 8 bits are set to 1, giving full intensity for that colour channel.
Tags: hexadecimal, colour codes, binary

**Item 10 [S]**
Question: Convert the decimal number 200 to hexadecimal.
Answer: 200 ÷ 16 = 12 remainder 8, so 200 = C8 in hexadecimal.
Difficulty: S
Topic: 2.4
Explanation: Divide by 16 repeatedly and record remainders. 200 divided by 16 gives 12 with remainder 8. 12 is C in hex. Read the result from bottom to top.
Tags: hexadecimal, decimal conversion

**Item 11 [S]**
Question: Why is hexadecimal more efficient than binary for representing IPv6 addresses?
Answer: An IPv6 address is 128 bits long. In binary this is 128 digits, which is extremely error-prone to read or write. In hexadecimal it is reduced to just 32 characters, making it manageable for humans to work with.
Difficulty: S
Topic: 2.4
Explanation: Hexadecimal shorthand compresses binary by a factor of 4. This efficiency becomes critical with long binary strings like IPv6 addresses, MAC addresses, and memory dumps.
Tags: hexadecimal, binary, efficiency, addresses

**Item 12 [S]**
Question: Convert the hexadecimal number 3E7 to binary.
Answer: 3E7 = 0011 1110 0111 in binary.
Difficulty: S
Topic: 2.4
Explanation: Convert each hex digit individually: 3 = 0011, E = 1110, 7 = 0111. Combine the groups to get the full binary representation.
Tags: hexadecimal, binary conversion

**Item 13 [C]**
Question: A programmer needs to represent a byte with the value 239. Explain why using hexadecimal (EF) rather than binary (11101111) is preferred in practical programming contexts.
Answer: Hexadecimal is preferred because it is shorter and less prone to transcription errors. A single hex digit is easier to verify visually than four binary digits. In codebases with thousands of memory addresses, colour values, and register configurations, the reduced visual complexity of hex significantly lowers the risk of mistakes. Additionally, each hex digit maps directly to 4 binary bits, so conversion is straightforward and unambiguous.
Difficulty: C
Topic: 2.4
Explanation: The binary representation 11101111 has eight digits that are difficult to verify by eye. The hex equivalent EF is two characters and can be checked at a glance. Many debugging tools and hex editors display data in hex precisely because of this human factors advantage.
Tags: hexadecimal, binary, programming, efficiency

**Item 14 [C]**
Question: Two hexadecimal values are added: 9A + 66. Perform the addition and explain the step-by-step process, including any carries.
Answer: Adding rightmost column: A + 6 = 10 + 6 = 16 = 10 (write 0, carry 1). Leftmost column: 9 + 6 + carry 1 = 16 = 10 (write 0, carry 1). Result is 100 in hex, which is 256 in decimal. Verification: 9A = 154, 66 = 102, 154 + 102 = 256 = 0x100.
Difficulty: C
Topic: 2.4
Explanation: Hex arithmetic follows the same rules as decimal but with base 16. Any column sum of 16 or more produces a carry to the next column, with the unit digit written and the tens digit carried.
Tags: hexadecimal, hex arithmetic, carries

**Item 15 [C]**
Question: Evaluate the claim that hexadecimal representation is unnecessary in modern programming because decimal is more intuitive for humans.
Answer: The claim is incorrect for technical contexts. Hexadecimal exists not as a human convenience but as a precise shorthand for binary, which is what computers actually process. Decimal does not map cleanly to binary boundaries — a decimal number like 100 requires converting all 7 bits of 1100100. Hexadecimal maps exactly to 4-bit boundaries, making it ideal for byte-level operations, bit masking, and low-level debugging. Modern debuggers, memory editors, and network tools continue to use hex precisely because it bridges the gap between human readability and binary precision.
Difficulty: C
Topic: 2.4
Explanation: Decimal intuition does not translate to binary accuracy. Hexadecimal's 16-symbol alphabet (0-9, A-F) aligns with the 4-bit boundary that underlies all byte-based computing, from network protocols to graphics programming.
Tags: hexadecimal, binary, evaluation, programming

**Item 16 [C]**
Question: A developer stores a white pixel as #FFFFFF and a light grey as #E5E5E5 in hexadecimal. Show the binary representation of both colours and explain how the slight change in hex produces a subtle visual difference.
Answer: #FFFFFF = 11111111 11111111 11111111 (all channels at maximum). #E5E5E5 = 11100101 11100101 11100101. Each channel differs slightly: Red: 11111111 vs 11100101 (difference of 10 decimal), Green and Blue: same reduction. The binary shows that each colour channel is reduced by approximately 6% from maximum, which in the display produces a light grey instead of pure white.
Difficulty: C
Topic: 2.4
Explanation: Hex notation makes it easy to see how individual colour channels are adjusted. The three pairs of hex digits clearly separate red, green, and blue components, allowing precise colour specification and adjustment.
Tags: hexadecimal, colour codes, binary, RGB

**Item 17 [C]**
Question: Explain how hexadecimal is used in debugging and memory inspection, and evaluate its effectiveness compared to decimal notation.
Answer: Debuggers and memory inspectors display raw memory contents in hex because it allows immediate recognition of byte patterns and alignment boundaries. A sequence like 00 00 00 00 FF FF FF FF immediately reveals a boundary between two 4-byte blocks — a pattern invisible in decimal (0 0 0 0 255 255 255 255). Hex also aligns perfectly with common data widths (8-bit bytes, 16-bit words, 32-bit double words), whereas decimal breaks alignment across these boundaries. The effectiveness is highest in low-level debugging, network packet analysis, and reverse engineering, where pattern recognition and bit-level operations are common.
Difficulty: C
Topic: 2.4
Explanation: Memory addresses increment in hex as 00, 01, 02... 0F, 10, 11... This natural alignment with power-of-2 boundaries makes hex the native language of memory inspection.
Tags: hexadecimal, debugging, memory addresses, binary

**Item 18 [C]**
Question: Convert the 8-bit binary number 10011010 to hexadecimal, then explain why the result can be interpreted differently depending on whether the number is treated as unsigned or signed in two's complement.
Answer: 10011010 = 9A in hexadecimal. As an unsigned number, 9A = 154 in decimal. As a signed two's complement number, the most significant bit is 1, indicating a negative value. The magnitude is calculated as -(256 - 154) = -102. The MSB being 1 means the number is negative, and the hex digit immediately signals this to a programmer reviewing a memory dump.
Difficulty: C
Topic: 2.4
Explanation: In two's complement, the MSB carries a negative weight. Hex notation makes it easy to spot whether the MSB hex digit is above 7 (negative in signed context) or below 8 (positive or zero). This is crucial for low-level programming and debugging.
Tags: hexadecimal, binary, two's complement, signed numbers
