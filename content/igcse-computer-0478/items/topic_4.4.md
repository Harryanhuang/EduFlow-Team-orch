# Topic 4.4 — Bubble Sort and Insertion Sort
## Items File

**Item 1 [F]**
Question: In a bubble sort, what is meant by a "pass" through the data?
Answer: A pass is one complete traversal of the list from the first element to the last, during which adjacent items are compared and swapped if they are in the wrong order.
Difficulty: F
Topic: 4.4
Explanation: During each pass, the largest unsorted element "bubbles up" to its correct position at the end of the list. The number of elements compared per pass decreases by one each time.
Tags: bubble sort, algorithm, pass

**Item 2 [F]**
Question: State one key difference between bubble sort and insertion sort.
Answer: Bubble sort repeatedly swaps adjacent items that are out of order. Insertion sort shifts items to make room for the next element, placing it in its correct sorted position.
Difficulty: F
Topic: 4.4
Explanation: Bubble sort works by pushing large values toward the end. Insertion sort works by pulling each new element into the sorted portion of the list.
Tags: bubble sort, insertion sort, comparison

**Item 3 [F]**
Question: What is the time complexity of bubble sort in the worst case?
Answer: O(n^2) — quadratic time.
Difficulty: F
Topic: 4.4
Explanation: In the worst case, every adjacent pair must be swapped, and this must be repeated for n passes. The number of comparisons grows with the square of the number of items.
Tags: bubble sort, complexity, big O

**Item 4 [F]**
Question: What does the term "in-place" mean when applied to sorting algorithms?
Answer: An in-place algorithm sorts data using only a small, fixed amount of additional memory that does not grow with the input size. It swaps elements within the original array rather than creating a new one.
Difficulty: F
Topic: 4.4
Explanation: Both bubble sort and insertion sort are in-place algorithms. They modify the original list rather than building a separate sorted copy.
Tags: sorting algorithms, in-place, memory

**Item 5 [F]**
Question: Write a pseudocode line that swaps the values of two variables A and B.
Answer: TEMP = A; A = B; B = TEMP.
Difficulty: F
Topic: 4.4
Explanation: A temporary variable is required to hold one value during the swap, otherwise both values would be overwritten and lost.
Tags: pseudocode, swap, variables

**Item 6 [F]**
Question: In insertion sort, what is the "sorted portion" of the list?
Answer: The sorted portion is the left-hand part of the list that has been placed in order. It grows by one element each time the next unsorted item is inserted into it.
Difficulty: F
Topic: 4.4
Explanation: Initially the sorted portion contains just the first element. With each iteration, one more element from the unsorted portion is taken and inserted into the correct position within the sorted portion.
Tags: insertion sort, sorted portion

**Item 7 [S]**
Question: Trace bubble sort on the list [5, 3, 8, 1] and show the state of the list after each pass.
Answer: Pass 1: [3, 5, 1, 8] → Pass 2: [3, 1, 5, 8] → Pass 3: [1, 3, 5, 8]. Sorted: [1, 3, 5, 8].
Difficulty: S
Topic: 4.4
Explanation: Pass 1 compares adjacent pairs: 5>3 swap, 5<8 no swap, 8>1 swap. Pass 2 continues with the reduced list. Pass 3 places the final element. The algorithm terminates early if no swaps occur in a pass.
Tags: bubble sort, trace, algorithm

**Item 8 [S]**
Question: Trace insertion sort on the list [5, 3, 8, 1] and show the state after each insertion.
Answer: Start with [5]. Insert 3: [3, 5, 8, 1]. Insert 8: [3, 5, 8, 1] (already in place). Insert 1: [1, 3, 5, 8]. Final sorted list: [1, 3, 5, 8].
Difficulty: S
Topic: 4.4
Explanation: For each element, shift elements in the sorted portion right until the correct gap is found, then insert. This mimics how people sort playing cards.
Tags: insertion sort, trace, algorithm

**Item 9 [S]**
Question: What is meant by a "flag" in the context of bubble sort optimisation?
Answer: A flag (sometimes called a "swapped" flag) tracks whether any swaps occurred during a pass. If no swaps are made, the list is already sorted and remaining passes can be skipped.
Difficulty: S
Topic: 4.4
Explanation: The flag is set to False at the start of each pass. If two elements are swapped, it is set to True. After the pass, if the flag is still False, the algorithm terminates.
Tags: bubble sort, optimisation, flag

**Item 10 [S]**
Question: Write pseudocode for a single pass of bubble sort.
Answer: SWAPPED = FALSE
FOR I = 0 TO N - 2
  IF List[I] > List[I+1] THEN
    TEMP = List[I]
    List[I] = List[I+1]
    List[I+1] = TEMP
    SWAPPED = TRUE
  ENDIF
ENDFOR
Difficulty: S
Topic: 4.4
Explanation: This compares each adjacent pair once. The loop runs from index 0 to n-2 because the last comparison is between elements at positions n-2 and n-1.
Tags: bubble sort, pseudocode, pass

**Item 11 [S]**
Question: Why does insertion sort generally perform fewer comparisons than bubble sort for partially sorted data?
Answer: In insertion sort, when an element is already larger than all elements in the sorted portion, no further comparisons are needed for that element. In bubble sort, every pass still checks all remaining adjacent pairs regardless of how sorted the list already is.
Difficulty: S
Topic: 4.4
Explanation: Insertion sort has best-case O(n) complexity when data is already sorted, checking only one comparison per element. Bubble sort's best case (with the flag optimisation) is O(n), but without it remains O(n^2).
Tags: insertion sort, bubble sort, comparison, best case

**Item 12 [S]**
Question: What is the time complexity of insertion sort in the worst case?
Answer: O(n^2) — quadratic time.
Difficulty: S
Topic: 4.4
Explanation: In the worst case (reverse-sorted data), each new element must be compared with every element already in the sorted portion and shifted all the way to the front. This produces a triangular number of comparisons.
Tags: insertion sort, complexity, big O

**Item 13 [C]**
Question: Write pseudocode for insertion sort and explain how the algorithm handles an element that needs to be placed at the very beginning of the sorted portion.
Answer: FOR I = 1 TO N-1
  Key = List[I]
  J = I - 1
  WHILE J >= 0 AND List[J] > Key
    List[J+1] = List[J]
    J = J - 1
  ENDWHILE
  List[J+1] = Key
ENDFOR
When the key is smaller than all existing sorted elements, the WHILE loop continues shifting elements right until J becomes -1. The final assignment List[J+1] = Key places the key at index 0.
Difficulty: C
Topic: 4.4
Explanation: The J >= 0 condition is critical — without it, the algorithm would attempt negative array indexing when inserting at position 0. This boundary condition distinguishes careful insertion sort from a naive implementation.
Tags: insertion sort, pseudocode, boundary condition

**Item 14 [C]**
Question: A developer has two arrays: one with 10,000 records that is almost in order (only 5 elements are out of place) and one with 10,000 completely random records. Recommend which sorting algorithm should be used for each and justify your choices.
Answer: For the nearly sorted array, use insertion sort. Insertion sort performs close to O(n) on nearly sorted data because each element is either already in position or only needs to move a few places. For the completely random array, insertion sort remains O(n^2), so bubble sort (also O(n^2)) is equally slow, but neither is ideal. Both cases would benefit from O(n log n) algorithms like quicksort or merge sort. However, between the two given options, insertion sort is the better general choice for the nearly sorted data, and for the random data both perform similarly in the worst case.
Difficulty: C
Topic: 4.4
Explanation: Insertion sort's adaptive nature makes it the preferred choice when data has partial order. Its in-place nature also means low memory overhead. For fully random large datasets, neither O(n^2) algorithm is appropriate.
Tags: bubble sort, insertion sort, algorithm selection, complexity

**Item 15 [C]**
Question: Critically compare bubble sort and insertion sort in terms of number of swaps, stability, and practical use.
Answer: Bubble sort performs more swaps because it swaps on every out-of-order comparison. Insertion sort shifts elements using array moves, which is often implemented as a single memory copy operation and is less expensive than swapping. Both are stable — equal elements never change relative order. In practice, insertion sort outperforms bubble sort in most cases because it does fewer writes and adapts to sorted input. Neither is used for large datasets where O(n log n) algorithms are preferred. Bubble sort has historical significance as a teaching tool but no significant practical advantages.
Difficulty: C
Topic: 4.4
Explanation: A stable sort preserves the order of equal elements, which matters when sorting records by multiple keys. Insertion sort's shift operations are typically more efficient than swap operations because they involve fewer memory writes.
Tags: bubble sort, insertion sort, comparison, stability, swaps

**Item 16 [C]**
Question: Trace bubble sort with a swapped flag on [3, 1, 2, 5, 4] and show how the flag causes early termination.
Answer: Pass 1: [1, 2, 3, 4, 5] — swaps occurred, flag set TRUE. Pass 2: [1, 2, 3, 4, 5] — no swaps, flag stays FALSE. Algorithm terminates here instead of continuing to passes 3 and 4. Without the flag, the algorithm would continue checking all passes even though the list was already sorted.
Difficulty: C
Topic: 4.4
Explanation: The swapped flag reduces bubble sort from O(n^2) in the worst case to O(n) in the best case (already sorted data). This is the standard optimisation taught for bubble sort.
Tags: bubble sort, flag, optimisation, trace

**Item 17 [C]**
Question: A student claims that bubble sort always takes the same number of comparisons regardless of the input order. Evaluate this statement.
Answer: The statement is incorrect only when the swapped flag optimisation is absent. Without the flag, bubble sort always performs n-1 comparisons in the first pass, n-2 in the second, and so on — the same regardless of input. However, with the swapped flag, if the list becomes sorted before all passes complete, remaining passes are skipped. A nearly sorted list may terminate after just one or two passes, performing far fewer comparisons than the worst case.
Difficulty: C
Topic: 4.4
Explanation: The unoptimised bubble sort is input-insensitive. The flag optimisation introduces input sensitivity, making bubble sort adaptive in the same way insertion sort is naturally adaptive without any special flag.
Tags: bubble sort, comparisons, optimisation, flag

**Item 18 [C]**
Question: Design a hybrid approach using insertion sort within bubble sort and explain what problem this solves.
Answer: A hybrid can use insertion sort for the last portion of the list where bubble sort becomes inefficient. Bubble sort is most effective at moving large elements to the correct position quickly but becomes slow for nearly sorted lists with small misplacements. Insertion sort excels at placing small misplaced elements. The hybrid runs bubble sort for the first k passes (where large elements are correctly positioned at the end), then switches to insertion sort for the remaining unsorted portion. This reduces the total number of comparisons and swaps compared to using either algorithm alone on large lists with many small out-of-order elements.
Difficulty: C
Topic: 4.4
Explanation: Hybrid algorithms exploit the complementary strengths of different sorting methods. This approach mirrors practical implementations in standard libraries, which often use insertion sort for small subarrays within quicksort or merge sort.
Tags: bubble sort, insertion sort, hybrid algorithm, optimisation
