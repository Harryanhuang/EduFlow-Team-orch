# Topic 3.2 — Boolean Algebra
## Items File

**Item 1 [F]**
Question: State the three basic logic gates and their symbols.
Answer: AND — output is 1 only when all inputs are 1. OR — output is 1 when at least one input is 1. NOT — output is the inverse of the input.
Difficulty: F
Topic: 3.2
Explanation: AND: flat-ended triangle with curved base. OR: curved shield shape. NOT: triangle with a small circle (bubble) at the output.
Tags: logic gates, AND, OR, NOT, symbols

**Item 2 [F]**
Question: What is the output of a NOT gate when the input is 1?
Answer: 0
Difficulty: F
Topic: 3.2
Explanation: NOT (inverter) flips the input: 0 → 1, 1 → 0. The small circle at the output represents inversion.
Tags: NOT gate, inverter, truth table

**Item 3 [F]**
Question: Draw the truth table for a 2-input AND gate.
Answer: | A | B | A·B |
|---|---|-----|
| 0 | 0 |  0  |
| 0 | 1 |  0  |
| 1 | 0 |  0  |
| 1 | 1 |  1  |
Difficulty: F
Topic: 3.2
Explanation: AND outputs 1 only when both inputs are 1. All other combinations give 0.
Tags: AND gate, truth table, 2-input

**Item 4 [F]**
Question: Draw the truth table for a 2-input OR gate.
Answer: | A | B | A+B |
|---|---|-----|
| 0 | 0 |  0  |
| 0 | 1 |  1  |
| 1 | 0 |  1  |
| 1 | 1 |  1  |
Difficulty: F
Topic: 3.2
Explanation: OR outputs 1 when at least one input is 1. Only 0,0 gives 0.
Tags: OR gate, truth table, 2-input

**Item 5 [F]**
Question: What are the two derived logic gates introduced in IGCSE Computer Science?
Answer: NAND (NOT-AND) and NOR (NOT-OR). NAND is an AND gate followed by a NOT gate. NOR is an OR gate followed by a NOT gate.
Difficulty: F
Topic: 3.2
Explanation: NAND and NOR are called universal gates because any other logic gate can be built from them. NAND outputs 0 only when both inputs are 1. NOR outputs 1 only when both inputs are 0.
Tags: NAND, NOR, derived gates, universal gates

**Item 6 [S]**
Question: Draw the truth table for a NAND gate with 2 inputs.
Answer: | A | B | NAND |
|---|---|------|
| 0 | 0 |  1  |
| 0 | 1 |  1  |
| 1 | 0 |  1  |
| 1 | 1 |  0  |
Difficulty: S
Topic: 3.2
Explanation: NAND is the inverse of AND. It outputs 0 only when both inputs are 1; all other cases output 1.
Tags: NAND, truth table, 2-input, derived gate

**Item 7 [S]**
Question: Simplify the Boolean expression A · 0.
Answer: 0
Difficulty: S
Topic: 3.2
Explanation: AND with 0 always gives 0, regardless of the other input. This is the Annulment law.
Tags: Boolean algebra, AND, simplification, annulment law

**Item 8 [S]**
Question: State and apply De Morgan's First Theorem.
Answer: The complement of A AND B equals NOT A OR NOT B: Ā·B̄ = A̅ + B̅
Difficulty: S
Topic: 3.2
Explanation: An AND gate can be replaced by an OR gate with inverted inputs. Example: Ā·B̄ for A=1, B=0: left side = 0·1 = 0; right side = 0+1 = 1? Wait, check: Ā = 0, B̅ = 1. Ā·B̄ = 0·1 = 0. A̅ = 0, B̅ = 1. A̅ + B̅ = 0+1 = 1. Still not equal. De Morgan's: Ā·B̄ = A̅ + B̅ means the complement of (A AND B) equals (NOT A) OR (NOT B). For A=1, B=0: (A AND B)=0, complement=1. (NOT A)=0, (NOT B)=1. OR=1. ✓.
Tags: De Morgan's law, Boolean algebra, complement, NAND equivalence

**Item 9 [S]**
Question: State and apply De Morgan's Second Theorem.
Answer: The complement of A OR B equals NOT A AND NOT B: A+B̅ = Ā · B̅
Difficulty: S
Topic: 3.2
Explanation: An OR gate can be replaced by an AND gate with inverted inputs. For A=1, B=0: (A+B) = 1, complement = 0. (NOT A)=0, (NOT B)=1. AND = 0. ✓.
Tags: De Morgan's law, Boolean algebra, complement, NOR equivalence

**Item 10 [S]**
Question: Simplify the Boolean expression A + A · B.
Answer: A
Difficulty: S
Topic: 3.2
Explanation: Using the Absorption law: A + A·B = A·(1 + B) = A·1 = A. Alternatively: A + A·B = A·(1 + B) = A. The term A absorbs A·B.
Tags: Boolean algebra, simplification, absorption law

**Item 11 [S]**
Question: What is the output of the circuit: input A → NOT gate → AND gate (with input B)?
Answer: Q = A̅ · B
Difficulty: S
Topic: 3.2
Explanation: Input A passes through NOT, becoming A̅. This then ANDs with B. The result is true (1) only when A is 0 and B is 1.
Tags: circuit analysis, NOT gate, AND gate, combinational logic

**Item 12 [S]**
Question: Simplify the Boolean expression A + A̅.
Answer: 1
Difficulty: S
Topic: 3.2
Explanation: A OR NOT A is always true (1). This is the Complement law: A + A̅ = 1.
Tags: Boolean algebra, complement law, simplification

**Item 13 [C]**
Question: Draw the truth table for a 3-input AND gate. How many rows does it have?
Answer: 8 rows (2³ = 8). The output is 1 only when all three inputs are 1.
Difficulty: C
Topic: 3.2
Explanation: A 3-input AND gate outputs 1 only when A=1, B=1, and C=1. All other combinations (7 rows) give 0.
Tags: AND gate, 3-input, truth table, combinational logic

**Item 14 [C]**
Question: Prove algebraically that A + A̅·B = A + B.
Answer: A + A̅·B = (A + A̅)·(A + B) [Distributive] = 1·(A + B) [Complement: A+A̅=1] = A + B [Identity: 1·X = X].
Difficulty: C
Topic: 3.2
Explanation: This is the Consensus theorem. The term A̅·B is redundant when A is already present in an OR term.
Tags: Boolean algebra, proof, distributive law, consensus theorem

**Item 15 [C]**
Question: Design a logic circuit for the Boolean expression Q = (A + B) · C̅.
Answer: OR gate (A, B) → AND gate (result, C̅). NOT gate on C feeds the AND gate.
Difficulty: C
Topic: 3.2
Explanation: First, NOT C to get C̅. Then OR A and B. Finally, AND the OR result with C̅.
Tags: logic circuit design, OR, AND, NOT, combinational circuit

**Item 16 [C]**
Question: Simplify the Boolean expression (A + B)·(A + C) using Boolean algebra.
Answer: A + B·C
Difficulty: C
Topic: 3.2
Explanation: Using distributive: (A+B)·(A+C) = A + A·C + B·A + B·C = A·(1+C+B) + B·C = A + B·C. Alternatively, the consensus term B·C remains.
Tags: Boolean algebra, simplification, distributive law, consensus

**Item 17 [C]**
Question: A logic circuit has inputs A and B. The output Q is 1 when the inputs are different. Identify the gate and write its Boolean expression.
Answer: XOR (Exclusive OR). Q = A ⊕ B = A·B̅ + A̅·B.
Difficulty: C
Topic: 3.2
Explanation: XOR outputs 1 for (0,1) and (1,0). Truth table: 00→0, 01→1, 10→1, 11→0. It is not a basic gate but can be built from AND, OR, and NOT.
Tags: XOR, exclusive OR, Boolean expression, logic gate

**Item 18 [C]**
Question: Prove that A·B + A̅·C + B·C = A·B + A̅·C using Boolean algebra.
Answer: A·B + A̅·C + B·C = A·B + A̅·C + B·C·(A+A̅) [since A+A̅=1] = A·B + A̅·C + A·B·C + A̅·B·C = A·B·(1+C) + A̅·C·(1+B) = A·B + A̅·C. The term B·C is redundant.
Difficulty: C
Topic: 3.2
Explanation: This is the Consensus theorem. The consensus term B·C is absorbed by the other two product terms and does not affect the output.
Tags: Boolean algebra, proof, consensus theorem, redundancy
