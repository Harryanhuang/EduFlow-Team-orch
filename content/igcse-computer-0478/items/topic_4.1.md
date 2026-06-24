# Topic 4.1 — Algorithm Design and Pseudocode
## Items File

**Item 1 [F]**
Question: State three properties that an algorithm must have.
Answer: (1) Finiteness: must terminate after a finite number of steps. (2) Definiteness: each step must be precisely and unambiguously defined. (3) Effectiveness: each step must be basic enough to be carried out exactly. (4) Input: may have zero or more inputs. (5) Output: must produce at least one output.
Difficulty: F
Topic: 4.1
Explanation: These five criteria define a proper algorithm. An algorithm must terminate (no infinite loops), be unambiguous (no vague instructions), and use operations that are simple enough to be performed exactly.
Tags: algorithm properties, finiteness, definiteness, computer science fundamentals

**Item 2 [F]**
Question: Trace and state the final value of X:
```
X ← 0
FOR I FROM 1 TO 4
  X ← X + I
ENDFOR
OUTPUT X
```
Answer: X = 10
Difficulty: F
Topic: 4.1
Explanation: Iteration trace: I=1 → X=0+1=1; I=2 → X=1+2=3; I=3 → X=3+3=6; I=4 → X=6+4=10. Final output: 10.
Tags: pseudocode, iteration, FOR loop, tracing, algorithm trace

**Item 3 [S]**
Question: Write pseudocode to input 10 numbers and output the largest.
Answer: ```
MAX ← −999999
FOR I FROM 1 TO 10
  INPUT N
  IF N > MAX THEN
    MAX ← N
  ENDIF
ENDFOR
OUTPUT MAX
```
Difficulty: S
Topic: 4.1
Explanation: Initialise MAX to a very small sentinel value so the first input is always larger. Each subsequent number is compared to MAX; if larger, MAX is updated. After 10 comparisons, MAX holds the largest of all 10 inputs.
Tags: pseudocode, linear search, maximum, iteration, selection

**Item 4 [S]**
Question: State the difference between WHILE and REPEAT-UNTIL loops. Give one use case for each.
Answer: WHILE: pre-test loop — condition checked BEFORE each iteration, may not execute at all. REPEAT-UNTIL: post-test loop — condition checked AFTER each iteration, always executes at least once.
Use WHILE: when the number of iterations depends on a condition that might already be false (e.g., searching until end of file). Use REPEAT-UNTIL: when the loop must run at least once (e.g., menu-driven program).
Difficulty: S
Topic: 4.1
Explanation: The key distinction is when the termination condition is evaluated. WHILE loops prevent zero-iteration scenarios; REPEAT-UNTIL loops guarantee at least one execution.
Tags: WHILE loop, REPEAT-UNTIL loop, pre-test, post-test, iteration

**Item 5 [S]**
Question: Draw a flowchart for: input mark, output "Pass" if mark ≥ 50 else "Fail".
Answer: Flowchart symbols: Oval (Start) → Parallelogram (Input mark) → Diamond (mark ≥ 50?) → "Pass" (Rectangle) → Oval (End); "Fail" (Rectangle) → Oval (End). Two branches from diamond: Yes → Pass; No → Fail.
Difficulty: S
Topic: 4.1
Explanation: Standard flowchart symbols: oval = terminal (start/end), parallelogram = input/output, rectangle = process, diamond = decision. The diamond has two labelled exits: Yes (condition true) and No (condition false).
Tags: flowchart, selection, IF-THEN-ELSE, decision symbol, algorithm design

**Item 6 [S]**
Question: Trace bubble sort on the list [5, 3, 8, 1] showing the state after each pass.
Answer: Pass 1: [3, 5, 1, 8] — 8 bubbled to the end. Pass 2: [3, 1, 5, 8] — 5 and 1 swapped. Pass 3: [1, 3, 5, 8] — 3 and 1 swapped. Sorted in 4 passes.
Difficulty: S
Topic: 4.1
Explanation: Bubble sort repeatedly compares adjacent pairs and swaps if out of order. Each complete pass places the next largest element in its correct final position. For n elements, at most n−1 passes are needed.
Tags: bubble sort, sorting algorithm, pseudocode, algorithm trace

**Item 7 [S]**
Question: Write pseudocode to check if a positive integer N is prime.
Answer: ```
INPUT N
IF N = 1 THEN
  OUTPUT "Not prime"
ELSE
  IS_PRIME ← TRUE
  FOR I FROM 2 TO N DIV 2
    IF N MOD I = 0 THEN
      IS_PRIME ← FALSE
      EXIT FOR
    ENDIF
  ENDFOR
  IF IS_PRIME = TRUE THEN
    OUTPUT "Prime"
  ELSE
    OUTPUT "Not prime"
  ENDIF
ENDIF
```
Difficulty: S
Topic: 4.1
Explanation: 1 is not prime by definition. For N > 1, test divisibility from 2 to N/2. If any divisor is found, IS_PRIME becomes FALSE and the loop exits early. Using N DIV 2 (not N−1) and EXIT FOR improves efficiency without changing correctness.
Tags: prime number, algorithm, pseudocode, divisibility, iteration

**Item 8 [S]**
Question: State two advantages of pseudocode over flowcharts.
Answer: (1) Pseudocode is easier to write and modify — just text editing vs redrawing diagrams. (2) Pseudocode maps more directly to actual code — each statement corresponds to a line of programming language.
Difficulty: S
Topic: 4.1
Explanation: Pseudocode bridges algorithm design and actual code. Flowcharts are visual and better for showing decision points and control flow. Pseudocode is better for detailed algorithm description.
Tags: pseudocode, flowchart, algorithm design, comparison

**Item 9 [S]**
Question: Trace binary search for target 23 in [2, 5, 8, 12, 15, 19, 23, 27, 31, 35].
Answer: L=0, U=9, Mid=(0+9)//2=4, ARR[4]=15. 23>15 → L=5. Mid=(5+9)//2=7, ARR[7]=27. 23<27 → U=6. Mid=(5+6)//2=5, ARR[5]=19. 23>19 → L=6. Mid=(6+6)//2=6, ARR[6]=23. Found at index 6. Steps: 4.
Difficulty: S
Topic: 4.1
Explanation: Binary search halves the range at each step. On sorted data with n=10 elements, binary search finds any target in at most ceil(log₂10)=4 steps. Linear search would need up to 10 steps in the worst case.
Tags: binary search, sorted array, searching algorithm, algorithm trace

**Item 10 [F]**
Question: State what a subroutine is and why it is used.
Answer: A subroutine is a named block of code that performs a specific task. It can be called from multiple places in a program. Uses: modularity, reusability, easier testing, and reduced code duplication.
Difficulty: F
Topic: 4.1
Explanation: Subroutines (functions or procedures) are the fundamental unit of decomposition. Each subroutine should perform one task. Parameters allow data to be passed in; return values allow results to be passed out.
Tags: subroutine, procedure, function, modular programming, code reuse

**Item 11 [F]**
Question: What is the difference between a procedure and a function in pseudocode?
Answer: A procedure performs an action (e.g., PRINT, MOVE). A function returns a value (e.g., MAX, SORT, CALCULATE). Procedures are called for their side effects; functions are called for their return values.
Difficulty: F
Topic: 4.1
Explanation: Both are subroutines. A function returns a value and can be used in expressions (e.g., X ← MAX(A,B)). A procedure changes state or performs output and cannot be used in an expression.
Tags: procedure, function, subroutine, difference, pseudocode

**Item 12 [F]**
Question: What is dry running an algorithm?
Answer: Dry running means executing an algorithm step by step on paper, recording the value of each variable at each step, to verify correctness before coding.
Difficulty: F
Topic: 4.1
Explanation: Dry running (tracing) is essential for debugging. Write the variable values in a table after each step. Compare with expected outputs. Detects logic errors early.
Tags: dry running, tracing, algorithm verification, desk checking

**Item 13 [S]**
Question: Write pseudocode to find the sum and average of 10 numbers.
Answer: ```
SUM ← 0
FOR I FROM 1 TO 10
  INPUT N
  SUM ← SUM + N
ENDFOR
AVG ← SUM / 10
OUTPUT "Sum =", SUM
OUTPUT "Average =", AVG
```
Difficulty: S
Topic: 4.1
Explanation: Accumulators (SUM) start at 0. Each input is added. After the loop, SUM holds the total. Average = SUM / 10. This separates accumulation (loop) from output (after loop).
Tags: accumulator, averaging, pseudocode, sequential algorithm

**Item 14 [S]**
Question: Explain why comments are important in pseudocode and algorithms.
Answer: Comments document what each section of code does, making the algorithm easier to understand, test, and maintain. They are ignored by the compiler/interpreter.
Difficulty: S
Topic: 4.1
Explanation: Good commenting practice: describe WHY, not just WHAT. Use comments to explain non-obvious logic, key decisions, and algorithm steps. Avoid over-commenting obvious operations.
Tags: comments, documentation, algorithm readability, best practices

**Item 15 [S]**
Question: Write pseudocode to swap two values A and B without using a temporary variable.
Answer: ```
A ← A + B
B ← A − B
A ← A − B
```
Difficulty: S
Topic: 4.1
Explanation: Mathematical trick: after line 1, A = A+B. After line 2, B = (A+B)−B = A. After line 3, A = (A+B)−A = B. Values are swapped without a temporary variable. Note: may cause overflow for very large integers.
Tags: swapping, arithmetic trick, pseudocode, variable exchange

**Item 16 [C]**
Question: Write pseudocode for linear search that returns the position of target T in array ARR[1..N] or reports "Not found".
Answer: ```
FOUND ← FALSE
INDEX ← 0
FOR I ← 1 TO N
  IF ARR[I] = T THEN
    FOUND ← TRUE
    INDEX ← I
    EXIT FOR
  ENDIF
ENDFOR
IF FOUND = TRUE THEN
  OUTPUT "Found at position", INDEX
ELSE
  OUTPUT "Not found"
ENDIF
```
Difficulty: C
Topic: 4.1
Explanation: Linear search checks every element until a match is found. EXIT FOR optimises by stopping early. Returns the first match position or reports not found. Time complexity: O(n).
Tags: linear search, array, pseudocode, algorithm design, searching

**Item 17 [C]**
Question: Write pseudocode to calculate the factorial of a non-negative integer N.
Answer: ```
INPUT N
IF N < 0 THEN
  OUTPUT "Invalid input"
ELSE
  FACT ← 1
  FOR I ← 2 TO N
    FACT ← FACT * I
  ENDFOR
  OUTPUT FACT
ENDIF
```
Difficulty: C
Topic: 4.1
Explanation: Factorial N! = N × (N−1) × ... × 1. Start with FACT = 1. Multiply by each integer from 2 to N. Handle N = 0! = 1 and N = 1! = 1 as special cases naturally (loop does not execute, FACT remains 1).
Tags: factorial, recursion, iterative algorithm, pseudocode

**Item 18 [C]**
Question: Compare linear search and binary search in terms of precondition, speed, and complexity.
Answer: Linear search: works on any array (unsorted OK), O(n) time, simple to implement. Binary search: requires sorted array (precondition), O(log n) time, faster for large datasets.
Difficulty: C
Topic: 4.1
Explanation: Binary search's speed advantage grows with n: n=1000: linear worst case = 1000, binary = 10. n=1000000: linear = 1000000, binary = 20. Binary search's requirement to maintain sorted order adds O(n log n) sort cost, which may outweigh binary search savings for small n.
Tags: linear search, binary search, comparison, time complexity, Big-O
