# Topic 5.1 — Variables and Data Types
## Items File

**Item 1 [F]**
Question: State three common data types used in programming.
Answer: (1) Integer — whole numbers (e.g., 42, −7, 0). (2) Real/Float — decimal numbers (e.g., 3.14, −0.5). (3) Char — single characters (e.g., 'A', 'x', '3'). (4) String — sequences of characters. (5) Boolean — TRUE or FALSE.
Difficulty: F
Topic: 5.1
Explanation: Each data type has different storage requirements. Integer = 2 or 4 bytes typically; Float = 4 or 8 bytes; Char = 1 byte. Using the correct type prevents overflow and improves memory efficiency.
Tags: data types, integer, float, string, boolean

**Item 2 [F]**
Question: What is the difference between a variable and a constant?
Answer: A variable can change value during program execution. A constant has a fixed value set once and cannot be changed. Constants protect against accidental modification.
Difficulty: F
Topic: 5.1
Explanation: Constants are named values like PI = 3.14159. If code accidentally tries to modify a constant, most compilers produce an error.
Tags: variable, constant, difference, programming

**Item 3 [F]**
Question: What is the result of 17 DIV 5 and 17 MOD 5 in integer arithmetic?
Answer: 17 DIV 5 = 3 (quotient), 17 MOD 5 = 2 (remainder)
Difficulty: F
Topic: 5.1
Explanation: 17 = 5×3 + 2. DIV gives the whole number part; MOD gives the remainder. Useful for checking divisibility and finding digit patterns.
Tags: DIV, MOD, integer division, remainder, modulo

**Item 4 [S]**
Question: Write pseudocode to input a name (string) and a score (integer) and output them.
Answer: ```
INPUT Name
INPUT Score
OUTPUT Name, " scored ", Score
```
Difficulty: S
Topic: 5.1
Explanation: Input statement reads from the user. Concatenation (joining strings) handles Name and Score together. Type checking at input ensures Score is read as an integer.
Tags: input, string, integer, pseudocode, data types

**Item 5 [S]**
Question: State three rules for naming variables.
Answer: (1) Must start with a letter or underscore (not a number). (2) Can only contain letters, digits, and underscores. (3) Cannot be a reserved keyword (e.g., IF, FOR, INPUT).
Difficulty: S
Topic: 5.1
Explanation: Valid names: Score1, _total, student_name. Invalid: 1stScore (starts with digit), my-score (hyphen not allowed), IF (reserved keyword). Most languages also prohibit spaces and special characters.
Tags: variable naming, identifiers, rules, programming conventions

**Item 6 [S]**
Question: What is the difference between global and local variables?
Answer: Global variables are accessible from anywhere in the program. Local variables are only accessible within the function or block where they are declared.
Difficulty: S
Topic: 5.1
Explanation: Global variables are declared outside all functions. Local variables are declared inside a procedure/function. Using local variables prevents unintended modifications from other parts of the program.
Tags: global variable, local variable, scope, programming

**Item 7 [S]**
Question: What is type conversion? Give one example.
Answer: Type conversion changes a value from one data type to another. Example: converting the string "123" to the integer 123.
Difficulty: S
Topic: 5.1
Explanation: Explicit conversion (CAST or TOSTRING/TOINT functions) prevents ambiguity. Implicit conversion occurs automatically (e.g., real = 5.0 when assigning integer 5 to a real variable).
Tags: type conversion, casting, data types, coercion

**Item 8 [S]**
Question: State two advantages of using meaningful variable names.
Answer: (1) Code is easier to understand and maintain. (2) Reduces bugs — it is clearer what each variable represents.
Difficulty: S
Topic: 5.1
Explanation: Meaningful names: totalScore, studentName. Meaningless names: x, temp2. Self-documenting code requires fewer comments.
Tags: variable names, readability, code quality

**Item 9 [S]**
Question: What is an array? Give one use case.
Answer: An array is an indexed collection of elements of the same data type. Use case: storing the marks of 30 students in a class (an array of 30 integers).
Difficulty: S
Topic: 5.1
Explanation: Array elements are accessed by index (array[1], array[2], etc.). All elements share the same name but have different positions. Efficient for iterating through related data.
Tags: array, indexed, collection, iteration

**Item 10 [F]**
Question: State the result of: (a) 25 DIV 4 (b) 25 MOD 4 (c) 100 MOD 7.
Answer: (a) 6 (b) 1 (c) 2
Difficulty: F
Topic: 5.1
Explanation: (a) 25÷4=6 r1 → DIV=6, MOD=1. (b) 25 MOD 4 = 1. (c) 100÷7=14 r2 → MOD=2.
Tags: DIV, MOD, integer arithmetic, remainder

**Item 11 [F]**
Question: What is the result of TRUE AND FALSE in Boolean logic?
Answer: FALSE
Difficulty: F
Topic: 5.1
Explanation: Boolean AND requires both operands to be TRUE for the result to be TRUE. TRUE AND FALSE = FALSE. OR needs only one TRUE. NOT inverts the Boolean value.
Tags: Boolean, AND, OR, NOT, logic

**Item 12 [F]**
Question: What is the result of NOT(NOT(TRUE))?
Answer: TRUE
Difficulty: F
Topic: 5.1
Explanation: NOT(TRUE) = FALSE, NOT(FALSE) = TRUE. Double negation cancels out.
Tags: NOT, Boolean logic, double negation

**Item 13 [S]**
Question: What is the difference between = and == in programming?
Answer: = is the assignment operator — it stores a value in a variable. == is the comparison operator — it tests whether two values are equal, returning TRUE or FALSE.
Difficulty: S
Topic: 5.1
Explanation: X ← 5 is assignment. X == 5 is a test: is X equal to 5? Confusing them is a common programming error.
Tags: assignment, comparison, operator, difference, common error

**Item 14 [S]**
Question: What is overflow in integer arithmetic?
Answer: Overflow occurs when the result of an arithmetic operation is too large or too small to fit in the allocated number of bits.
Difficulty: S
Topic: 5.1
Explanation: In an 8-bit unsigned integer, 255 + 1 = 0 (wraps around). In signed two's complement, 127 + 1 = −128. Many languages silently overflow or raise errors.
Tags: overflow, integer limits, binary arithmetic, error

**Item 15 [S]**
Question: Declare an array MARKS[1..10] of integers and initialise it to all zeros.
Answer: DECLARE MARKS[1..10] OF INTEGER; FOR I ← 1 TO 10: MARKS[I] ← 0; ENDFOR
Difficulty: S
Topic: 5.1
Explanation: Declaration allocates space. Initialisation sets all elements to 0. Uninitialised arrays may contain garbage values.
Tags: array, declaration, initialisation, pseudocode

**Item 16 [S]**
Question: What is the difference between a one-dimensional array and a two-dimensional array?
Answer: 1D array: a list of values indexed by position. 2D array: a table of values indexed by row and column (a grid/matrix).
Difficulty: S
Topic: 5.1
Explanation: Example 1D: temperatures[1..7] stores one week's temperatures. Example 2D: board[1..3][1..3] stores a tic-tac-toe grid. 2D arrays are accessed with two indices: board[2][3].
Tags: 1D array, 2D array, matrix, indexed

**Item 17 [C]**
Question: Write pseudocode to find the minimum value in an integer array MARKS[1..N].
Answer: ```
MIN ← MARKS[1]
FOR I ← 2 TO N
  IF MARKS[I] < MIN THEN
    MIN ← MARKS[I]
  ENDIF
ENDFOR
OUTPUT MIN
```
Difficulty: C
Topic: 5.1
Explanation: Initialise MIN to the first element. Compare each subsequent element, updating MIN whenever a smaller value is found. This is O(n) — one pass through the array.
Tags: minimum, array, linear search, algorithm, iteration

**Item 18 [C]**
Question: A student record has fields: Name (string), Age (integer), Score (real). Write pseudocode to input and output a student record.
Answer: ```
RECORD Student
  DECLARE Name: STRING
  DECLARE Age: INTEGER
  DECLARE Score: REAL
ENDRECORD
DECLARE Student1: Student
INPUT Student1.Name
INPUT Student1.Age
INPUT Student1.Score
OUTPUT Student1.Name, Student1.Age, Student1.Score
```
Difficulty: C
Topic: 5.1
Explanation: A record (struct) groups related fields of different types. Access individual fields using dot notation. Records are essential for data structures like linked lists and binary trees.
Tags: record, struct, composite type, fields, data structure
