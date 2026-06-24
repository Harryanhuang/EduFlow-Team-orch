# Topic 5.3 — Procedures and Functions
## Items File

**Item 1 [F]**
Question: What is a procedure in programming?
Answer: A procedure is a named block of code that performs a specific task. It is called by its name and may accept input parameters but does not return a value.
Difficulty: F
Topic: 5.3
Explanation: Procedures are used to organise code, avoid repetition, and break a program into manageable sections.
Tags: procedure, subroutine, modular programming

**Item 2 [F]**
Question: What is a function in programming?
Answer: A function is a named block of code that performs a calculation and returns a value to the calling code.
Difficulty: F
Topic: 5.3
Explanation: Unlike a procedure, a function is called as part of an expression and produces a return value. Example: `result ← SquareRoot(16)` assigns 4.
Tags: function, return value, subroutine

**Item 3 [F]**
Question: State one advantage of using procedures and functions.
Answer: Code reusability — the same procedure or function can be called multiple times from different parts of the program without rewriting the code.
Difficulty: F
Topic: 5.3
Explanation: Without procedures/functions, the same code would be copied multiple times, making the program longer and harder to maintain.
Tags: advantage, reusability, modular programming

**Item 4 [F]**
Question: What is a parameter (argument) in the context of procedures and functions?
Answer: A parameter is a variable or value passed to a procedure or function when it is called, to provide input data for the routine to work on.
Difficulty: F
Topic: 5.3
Explanation: Example: Square(n) receives n as a parameter. When called as Square(5), n receives the value 5.
Tags: parameter, argument, input, subroutine

**Item 5 [S]**
Question: What is the difference between a parameter and a return value?
Answer: A parameter passes data into a procedure/function. A return value passes the result back out to the calling code.
Difficulty: S
Topic: 5.3
Explanation: Parameters are inputs (read by the routine). Return values are outputs (produced by functions and sent back to the caller).
Tags: parameter, return value, input, output

**Item 6 [S]**
Question: What is meant by "calling" a procedure or function?
Answer: Calling means invoking the procedure or function by name during program execution, causing its code to run.
Difficulty: S
Topic: 5.3
Explanation: After the routine completes, execution resumes at the statement immediately after the call.
Tags: procedure call, function call, invocation

**Item 7 [S]**
Question: What is a local variable?
Answer: A local variable is one that is declared inside a procedure or function. It only exists during the execution of that routine and cannot be accessed outside it.
Difficulty: S
Topic: 5.3
Explanation: Local variables prevent interference between different routines. When the routine ends, its local variables are destroyed.
Tags: local variable, scope, lifetime, procedure

**Item 8 [S]**
Question: What is a global variable? Give one disadvantage.
Answer: A global variable is declared outside all procedures and functions, accessible from anywhere in the program. Disadvantage: it can be accidentally modified by any routine, leading to hard-to-find bugs.
Difficulty: S
Topic: 5.3
Explanation: Example: a counter incremented by multiple procedures. If one procedure modifies it unexpectedly, all procedures see the changed value.
Tags: global variable, scope, disadvantage, shared state

**Item 9 [S]**
Question: Write pseudocode for a procedure that outputs "Hello, World!".
Answer: ```
PROCEDURE Greet
  OUTPUT "Hello, World!"
ENDPROCEDURE
```
Difficulty: S
Topic: 5.3
Explanation: A procedure is defined once with PROCEDURE...ENDPROCEDURE. It is called by its name: Greet.
Tags: procedure, definition, pseudocode, basic

**Item 10 [S]**
Question: Write pseudocode for a function that calculates the area of a rectangle.
Answer: ```
FUNCTION Area(length, width)
  RETURN length * width
ENDFUNCTION
```
Difficulty: S
Topic: 5.3
Explanation: The function accepts two parameters (length and width), multiplies them, and returns the result. Called as: a ← Area(5, 3).
Tags: function, parameters, RETURN, area calculation

**Item 11 [S]**
Question: What is a subroutine? How does it relate to procedures and functions?
Answer: A subroutine is the general term for a named block of code that can be called from elsewhere. Procedures and functions are both types of subroutines.
Difficulty: S
Topic: 5.3
Explanation: In some contexts, "subroutine" refers to any callable routine. In others, it specifically means a procedure (no return value).
Tags: subroutine, procedure, function, terminology

**Item 12 [S]**
Question: State one use case for a procedure with no parameters.
Answer: Initialising the screen display or printing a menu — actions that are always the same and do not need external input.
Difficulty: S
Topic: 5.3
Explanation: Procedures can be used for self-contained tasks: PRINTMENU, CLEARDISPLAY, SHOWERROR. They are called for their side effects, not their return values.
Tags: procedure, no parameters, use case

**Item 13 [C]**
Question: Write pseudocode for a function that checks whether a number is prime.
Answer: ```
FUNCTION IsPrime(n)
  IF n < 2 THEN RETURN FALSE
  FOR i ← 2 TO n DIV 2
    IF n MOD i = 0 THEN RETURN FALSE
  ENDFOR
  RETURN TRUE
ENDFUNCTION
```
Difficulty: C
Topic: 5.3
Explanation: If n < 2, not prime. For each i from 2 to n/2, if n is divisible by i, not prime. If no divisor found, prime.
Tags: function, prime, algorithm, pseudocode

**Item 14 [C]**
Question: Explain why using global variables is generally discouraged.
Answer: Global variables create hidden dependencies between routines — any function could modify them, making the program's behaviour unpredictable and debugging difficult.
Difficulty: C
Topic: 5.3
Explanation: Good practice: pass data as parameters and return results. This makes each routine self-contained and easier to test.
Tags: global variable, disadvantage, encapsulation, programming practice

**Item 15 [C]**
Question: Write pseudocode for a procedure that takes two parameters (name and age) and outputs a personalised greeting.
Answer: ```
PROCEDURE Greet(name, age)
  OUTPUT "Hello " + name + ", you are " + age + " years old."
ENDPROCEDURE
```
Difficulty: C
Topic: 5.3
Explanation: Called as: Greet("Alice", 15). The parameters name and age receive the values "Alice" and 15 respectively.
Tags: procedure, parameters, string concatenation, pseudocode

**Item 16 [C]**
Question: What is meant by "passing by value" versus "passing by reference"?
Answer: Pass by value: a copy of the variable's value is passed — changes inside the routine do not affect the original. Pass by reference: the variable's memory address is passed — changes affect the original.
Difficulty: C
Topic: 5.3
Explanation: In pseudocode: passing by value is the default. Passing by reference is indicated by keywords like BYREF or by using pointers.
Tags: pass by value, pass by reference, parameter passing, reference

**Item 17 [C]**
Question: Write a function that calculates the factorial of n using recursion.
Answer: ```
FUNCTION Factorial(n)
  IF n ≤ 1 THEN RETURN 1
  RETURN n * Factorial(n − 1)
ENDFUNCTION
```
Difficulty: C
Topic: 5.3
Explanation: Base case: n ≤ 1 returns 1. Recursive case: n * Factorial(n−1). For n=5: 5*4*3*2*1 = 120.
Tags: recursion, function, factorial, base case

**Item 18 [C]**
Question: What is a stack overflow in the context of recursive functions? When does it occur?
Answer: Stack overflow occurs when recursive calls use more memory than is available on the call stack. It happens when there is no base case or the recursion is too deep.
Difficulty: C
Topic: 5.3
Explanation: Each recursive call adds a new stack frame. If Factorial(1000000) is called, a million stack frames are allocated, exhausting memory.
Tags: stack overflow, recursion, memory, base case
