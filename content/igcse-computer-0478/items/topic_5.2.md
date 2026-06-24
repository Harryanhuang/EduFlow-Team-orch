# Topic 5.2 — Sequence, Selection, and Iteration
## Items File

**Item 1 [F]**
Question: What is meant by "sequence" in programming?
Answer: Sequence means the program executes instructions one after another in the order they are written.
Difficulty: F
Topic: 5.2
Explanation: Each instruction is executed completely before the next one begins. Changing the order changes the program's behaviour.
Tags: sequence, program structure, order of execution

**Item 2 [F]**
Question: What is a selection structure in programming?
Answer: Selection allows the program to choose between two or more paths based on a condition. The common types are IF...THEN...ELSE and CASE statements.
Difficulty: F
Topic: 5.2
Explanation: Without selection, programs could only follow one fixed path. Selection makes programs responsive to different inputs and states.
Tags: selection, IF-THEN-ELSE, CASE, branching

**Item 3 [F]**
Question: State three types of iteration (loop) structures.
Answer: (1) FOR loop — repeats a known number of times. (2) WHILE loop — repeats while a condition is true. (3) REPEAT...UNTIL loop — repeats until a condition becomes true.
Difficulty: F
Topic: 5.2
Explanation: All three allow code to be executed repeatedly. The choice depends on whether the number of iterations is known in advance.
Tags: iteration, loops, FOR, WHILE, REPEAT

**Item 4 [F]**
Question: Write pseudocode for an IF...THEN...ELSE statement.
Answer: ```
IF condition = TRUE THEN
  // statements when true
ELSE
  // statements when false
ENDIF
```
Difficulty: F
Topic: 5.2
Explanation: The condition is evaluated as TRUE or FALSE. Exactly one branch executes — either the THEN block or the ELSE block.
Tags: IF-THEN-ELSE, selection, pseudocode

**Item 5 [S]**
Question: What is the key difference between a WHILE loop and a REPEAT...UNTIL loop?
Answer: WHILE checks the condition at the start — the loop body may never execute. REPEAT...UNTIL checks at the end — the loop body always executes at least once.
Difficulty: S
Topic: 5.2
Explanation: WHILE: pre-test loop. REPEAT: post-test loop. Use WHILE when zero iterations may be needed. Use REPEAT when at least one iteration is required.
Tags: WHILE loop, REPEAT loop, pre-test, post-test

**Item 6 [S]**
Question: Write pseudocode for a FOR loop that outputs the numbers 1 to 10.
Answer: ```
FOR I ← 1 TO 10
  OUTPUT I
ENDFOR
```
Difficulty: S
Topic: 5.2
Explanation: The loop variable I starts at 1 and increments by 1 each iteration until it reaches 10.
Tags: FOR loop, pseudocode, iteration, 1 to 10

**Item 7 [S]**
Question: What is an infinite loop? Give one example in pseudocode.
Answer: An infinite loop never terminates because the terminating condition is never met. Example: REPEAT OUTPUT "hello" UNTIL FALSE (never becomes true).
Difficulty: S
Topic: 5.2
Explanation: Infinite loops cause programs to hang. Common causes: forgetting to update the loop variable, or setting the condition so it never changes.
Tags: infinite loop, REPEAT loop, termination, bug

**Item 8 [S]**
Question: What is the purpose of a CASE statement compared to nested IF statements?
Answer: CASE is clearer and more efficient when testing one variable against multiple possible values. Nested IFs are harder to read and slower.
Difficulty: S
Topic: 5.2
Explanation: CASE selects one branch from many based on the value of a single expression. It is equivalent to a chain of IF...ELSE IF...ELSE.
Tags: CASE statement, selection, multiple conditions

**Item 9 [S]**
Question: Write pseudocode for a REPEAT...UNTIL loop that doubles a number until it exceeds 1000.
Answer: ```
value ← 1
REPEAT
  value ← value * 2
UNTIL value > 1000
OUTPUT value
```
Difficulty: S
Topic: 5.2
Explanation: Initial value = 1. Each iteration doubles: 1→2→4→8→16→32→64→128→256→512→1024. Loop exits when 1024 > 1000. Output: 1024.
Tags: REPEAT loop, pseudocode, doubling, until condition

**Item 10 [S]**
Question: What is a nested selection? Give an example.
Answer: A nested selection is a selection structure inside another selection structure. Example: an IF inside another IF.
Difficulty: S
Topic: 5.2
Explanation: Example: IF age >= 18 THEN IF age >= 65 THEN OUTPUT "senior" ELSE OUTPUT "adult" ENDIF ELSE OUTPUT "minor" ENDIF. Nesting allows multi-level decision-making.
Tags: nested IF, selection, multi-level decision

**Item 11 [S]**
Question: How many times does the following loop execute? FOR I ← 5 TO 10.
Answer: 6 times (when I = 5, 6, 7, 8, 9, 10).
Difficulty: S
Topic: 5.2
Explanation: From 5 to 10 inclusive is 10 − 5 + 1 = 6 iterations.
Tags: FOR loop, iteration count, loop bounds

**Item 12 [S]**
Question: Write pseudocode using a WHILE loop to find the smallest power of 2 greater than 1000.
Answer: ```
n ← 0
WHILE 2^n ≤ 1000
  n ← n + 1
ENDWHILE
OUTPUT 2^n
```
Difficulty: S
Topic: 5.2
Explanation: Starting from n=1 (2): values tested: 2,4,8,16,32,64,128,256,512,1024. Loop exits when 2^n > 1000. n=10, output 1024.
Tags: WHILE loop, power of 2, pseudocode

**Item 13 [C]**
Question: Write pseudocode for a program that inputs 10 numbers and outputs the largest.
Answer: ```
INPUT max
FOR I ← 2 TO 10
  INPUT num
  IF num > max THEN
    max ← num
  ENDIF
ENDFOR
OUTPUT max
```
Difficulty: C
Topic: 5.2
Explanation: Initialise max with the first number. Compare each subsequent number and update max if a larger value is found. This is O(n).
Tags: FOR loop, WHILE loop, selection, maximum value

**Item 14 [C]**
Question: A WHILE loop condition is never true initially. What happens to the loop body?
Answer: The loop body never executes — the condition is checked first, and if false, the loop is skipped entirely.
Difficulty: C
Topic: 5.2
Explanation: This is the key difference from REPEAT...UNTIL. A pre-test loop may execute zero times; a post-test loop always executes at least once.
Tags: WHILE loop, pre-test, zero iterations

**Item 15 [C]**
Question: Write pseudocode using a WHILE loop to calculate the factorial of n.
Answer: ```
INPUT n
factorial ← 1
WHILE n > 0
  factorial ← factorial * n
  n ← n − 1
ENDWHILE
OUTPUT factorial
```
Difficulty: C
Topic: 5.2
Explanation: For n=5: 1×5=5, 5×4=20, 20×3=60, 60×2=120, 120×1=120. Output: 120.
Tags: WHILE loop, factorial, iteration, multiplication

**Item 16 [C]**
Question: Explain why infinite loops are dangerous and how to prevent them.
Answer: Infinite loops cause programs to freeze, consuming CPU and memory until manually terminated. Prevention: ensure the loop variable is updated, or the terminating condition is guaranteed to be reached.
Difficulty: C
Topic: 5.2
Explanation: Common causes: forgetting `n ← n − 1` in a WHILE loop, or setting a REPEAT condition to a value that never changes.
Tags: infinite loop, bug, prevention, loop variable

**Item 17 [C]**
Question: Write pseudocode for a CASE statement that outputs a grade based on a percentage score.
Answer: ```
CASE OF score
  ≥ 80: OUTPUT "A"
  ≥ 70: OUTPUT "B"
  ≥ 60: OUTPUT "C"
  ≥ 50: OUTPUT "D"
  < 50: OUTPUT "F"
ENDCASE
```
Difficulty: C
Topic: 5.2
Explanation: CASE evaluates score once and selects the matching branch. The order matters — conditions are checked top to bottom.
Tags: CASE, selection, grade, percentage

**Item 18 [C]**
Question: Compare the three iteration structures in terms of when they should be used.
Answer: Use FOR when the number of iterations is known. Use WHILE when the loop may not execute at all (pre-test needed). Use REPEAT when at least one execution is required (post-test).
Difficulty: C
Topic: 5.2
Explanation: Choosing the correct loop type improves readability and prevents errors. FOR implies counting; WHILE implies condition-based continuation.
Tags: iteration comparison, FOR, WHILE, REPEAT, when to use
