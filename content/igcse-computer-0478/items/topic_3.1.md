# Topic 3.1 — Logic Gates and Boolean Algebra
## Items File

**Item 1 [F]**
Question: Draw the standard logic gate symbols for AND, OR, NOT, NAND, and NOR.
Answer: AND: flat-backed D shape (inputs top+bottom, output right); OR: curved shield shape; NOT: triangle with circle at output; NAND: AND gate with circle at output; NOR: OR gate with circle at output.
Difficulty: F
Topic: 3.1
Explanation: Standard IEEE/ANSI logic gate symbols: AND has a flat back edge; OR has a curved shield shape; NOT has a small circle (bubble) at the output indicating inversion; NAND adds a bubble to AND; NOR adds a bubble to OR. All gates conventionally have inputs on the left and output on the right.
Tags: logic gates, AND, OR, NOT, NAND, NOR, symbols

**Item 2 [F]**
Question: Complete the truth table for a NOT gate with input A and output Q.
Answer: | A | Q |; | 0 | 1 |; | 1 | 0 |
Difficulty: F
Topic: 3.1
Explanation: A NOT gate (inverter) outputs the opposite of its input. The small circle (bubble) at the output indicates logical negation. If A = 0, Q = 1. If A = 1, Q = 0.
Tags: NOT gate, truth table, inversion, logic gates

**Item 3 [S]**
Question: Draw the truth table for Q = A AND NOT B.
Answer: | A | B | NOT B | Q |; | 0 | 0 | 1 | 0 |; | 0 | 1 | 0 | 0 |; | 1 | 0 | 1 | 1 |; | 1 | 1 | 0 | 0 |
Difficulty: S
Topic: 3.1
Explanation: First compute NOT B, then AND with A. Q = A · NOT B. Q = 1 only when A = 1 AND NOT B = 1, which means A = 1 and B = 0. Only the third row satisfies this condition.
Tags: logic gates, AND, NOT, truth table, Boolean expression

**Item 4 [S]**
Question: For the circuit: input A → NOT gate → AND gate (second input B) → output Q. Write the Boolean expression and simplify.
Answer: Q = A̅ · B (A NOT B AND B)
Difficulty: S
Topic: 3.1
Explanation: A passes through the NOT gate first, becoming A̅. Then A̅ and B are the two inputs to the AND gate. The Boolean expression is Q = A̅ · B. This cannot be simplified further using basic Boolean laws.
Tags: Boolean expression, NOT gate, AND gate, circuit analysis

**Item 5 [S]**
Question: Using De Morgan's Laws, write equivalent expressions for: (a) NOT(A OR B) (b) NOT(A AND B).
Answer: (a) NOT(A OR B) = NOT A AND NOT B; (b) NOT(A AND B) = NOT A OR NOT B
Difficulty: S
Topic: 3.1
Explanation: De Morgan's Laws: (1) ¬(A ∨ B) = ¬A ∧ ¬B. (2) ¬(A ∧ B) = ¬A ∨ ¬B. These are fundamental for simplifying logic circuits and converting between NAND/NOR-only implementations.
Tags: De Morgan's laws, Boolean algebra, complement, logic gates

**Item 6 [S]**
Question: Draw the truth table for Q = (A AND B) OR (NOT A). State when Q = 1.
Answer: | A | B | A·B | NOT A | Q |; | 0 | 0 | 0 | 1 | 1 |; | 0 | 1 | 0 | 1 | 1 |; | 1 | 0 | 0 | 0 | 0 |; | 1 | 1 | 1 | 0 | 1 |. Q = 1 when A = 0 (any B) or when A = 1 and B = 1.
Difficulty: S
Topic: 3.1
Explanation: Compute A·B and NOT A separately, then OR them. Q = 1 when either term is 1. When A = 0: NOT A = 1, so Q = 1 regardless of A·B. When A = 1: NOT A = 0, so Q = A·B (only 1 when B = 1).
Tags: Boolean expression, truth table, AND, OR, NOT, logic circuit

**Item 7 [S]**
Question: What is the purpose of a buffer in a logic circuit?
Answer: A buffer amplifies a signal, restoring it to full voltage/current levels after degradation through long wires or many gate inputs.
Difficulty: S
Topic: 3.1
Explanation: A buffer is essentially two NOT gates in series (Q = NOT(NOT A) = A). It restores signal strength lost through wire resistance and capacitance. It also provides fan-out: each logic gate output can only drive a limited number of inputs; buffers increase drive capability.
Tags: buffer, signal restoration, fan-out, logic gates

**Item 8 [S]**
Question: State the truth table for an XOR gate.
Answer: | A | B | Q |; | 0 | 0 | 0 |; | 0 | 1 | 1 |; | 1 | 0 | 1 |; | 1 | 1 | 0 |
Difficulty: S
Topic: 3.1
Explanation: XOR (exclusive OR) outputs 1 when exactly one input is 1. XOR is used in addition (half adder), parity checking, and controlled switching. It can be implemented from basic gates as (A + B) · NOT(A · B).
Tags: XOR gate, truth table, exclusive OR, logic gates

**Item 9 [S]**
Question: A logic circuit has inputs A and B. Output Q = 1 when exactly one input is 1. What gate is this and draw the truth table.
Answer: XOR gate. | A | B | Q |; | 0 | 0 | 0 |; | 0 | 1 | 1 |; | 1 | 0 | 1 |; | 1 | 1 | 0 |
Difficulty: S
Topic: 3.1
Explanation: "Exactly one input is 1" defines the XOR operation. XOR = exclusive OR. Q = 1 when inputs differ. This is the definition used in binary addition (half adder sum bit).
Tags: XOR gate, exclusive OR, truth table, logic gates

**Item 10 [F]**
Question: Complete the truth table for a NAND gate.
Answer: | A | B | Q |; | 0 | 0 | 1 |; | 0 | 1 | 1 |; | 1 | 0 | 1 |; | 1 | 1 | 0 |
Difficulty: F
Topic: 3.1
Explanation: NAND = NOT (A AND B). NAND outputs 0 only when both inputs are 1. It is a universal gate — any other logic gate can be built from NAND gates alone.
Tags: NAND gate, truth table, universal gate, logic gates

**Item 11 [F]**
Question: State two advantages of using NAND gates over other gates.
Answer: (1) NAND is a universal gate — any Boolean function can be implemented using only NAND gates. (2) NAND gates are typically faster and use fewer transistors in CMOS technology than implementations using AND followed by NOT.
Difficulty: F
Topic: 3.1
Explanation: A NAND gate can implement NOT (by tying inputs together), AND (by NAND followed by NOT), OR (by NOT A NAND NOT B), and any other Boolean function. This means only NAND gates are needed in a chip design.
Tags: NAND gate, universal gate, advantages, transistor count

**Item 12 [F]**
Question: Draw the circuit for Q = A XOR B using only NAND gates.
Answer: NAND(A, B) NAND NAND(A, A) NAND NAND(B, B) → Q. (Or: 4 NAND gates: G1 = NAND(A,B); G2 = NAND(A,G1); G3 = NAND(B,G1); Q = NAND(G2,G3).)
Difficulty: F
Topic: 3.1
Explanation: XOR can be built from NAND as: Q = NAND(NAND(A, NAND(A,B)), NAND(B, NAND(A,B)). Alternatively: Q = (A NAND B) NAND (A NAND A) NAND (B NAND B) using three NANDs.
Tags: NAND implementation, XOR, Boolean algebra, logic circuits

**Item 13 [S]**
Question: Using Boolean algebra, simplify: (A + A̅ · B)
Answer: A + A̅ · B = A + B
Difficulty: S
Topic: 3.1
Explanation: Using the distributive law: A + A̅ · B = (A + A̅)(A + B) = 1 · (A + B) = A + B. This is the consensus theorem. The consensus term B is eliminated because A already covers the case where A = 1.
Tags: Boolean algebra, simplification, consensus theorem, distributive law

**Item 14 [S]**
Question: What is a flip-flop and why is it important in computing?
Answer: A flip-flop is a bistable circuit that stores one bit of memory (0 or 1). It maintains its output state until explicitly changed by inputs. Flip-flops are the fundamental building blocks of registers and memory.
Difficulty: S
Topic: 3.1
Explanation: Flip-flops (SR, D, JK, T types) are sequential logic elements. Unlike combinational logic (output depends only on current inputs), flip-flops have memory — their output depends on past inputs and the clock signal. They form registers, RAM, and state machines.
Tags: flip-flop, bistable, memory, registers, sequential logic

**Item 15 [S]**
Question: Explain the purpose of a clock signal in a digital circuit.
Answer: A clock signal provides a regular timing pulse that synchronises operations in sequential logic circuits, ensuring flip-flops and registers change state at precisely defined moments.
Difficulty: S
Topic: 3.1
Explanation: The clock is a square wave oscillator. Flip-flops read their inputs on the rising or falling edge of the clock pulse, ensuring all operations occur in a coordinated, predictable sequence. Without a clock, different parts of the circuit would operate asynchronously, causing race conditions.
Tags: clock, synchronisation, sequential circuits, timing, digital electronics

**Item 16 [C]**
Question: A logic circuit has output Q = (A + B̅) · B. Simplify using Boolean algebra and state the result.
Answer: Q = A·B + B̅
Difficulty: C
Topic: 3.1
Explanation: Q = (A + B̅) · B = A·B + B̅·B (distributive). B̅·B = 0 (since B + B̅ = 1 and B·B̅ = 0). So Q = A·B + 0 = A·B. The expression simplifies to A AND B.
Tags: Boolean algebra, simplification, distributive law, logic circuit

**Item 17 [C]**
Question: Draw the circuit for Q = A XOR B using AND, OR, and NOT gates. Derive the expression from truth table.
Answer: XOR = (A · B̅) + (A̅ · B). Circuit: A → NOT → AND with B; B → NOT → AND with A; both AND outputs → OR gate → Q.
Difficulty: C
Topic: 3.1
Explanation: From the XOR truth table, Q = 1 for rows 2 and 3 (exactly one input = 1). Row 2 (A=0, B=1): Q = A̅ · B. Row 3 (A=1, B=0): Q = A · B̅. By the sum of products method: Q = A̅B + AB̅. Implemented as two AND gates and one OR gate.
Tags: XOR gate, circuit design, sum of products, combinational logic

**Item 18 [C]**
Question: Design a half adder circuit: inputs A and B, outputs S (sum) and C (carry). Derive Boolean expressions and draw the circuit.
Answer: Sum: S = A XOR B = A̅B + AB̅. Carry: C = A AND B. Circuit: XOR gate for S; AND gate for C.
Difficulty: C
Topic: 3.1
Explanation: Half adder adds two bits. Sum bit (S) is 1 when exactly one input is 1 (XOR). Carry bit (C) is 1 when both inputs are 1 (AND). Full adder extends this with carry-in input. The half adder is the basic building block of binary addition in the ALU.
Tags: half adder, XOR, AND, ALU, binary addition, circuit design
