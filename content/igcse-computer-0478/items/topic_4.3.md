# Topic 4.3 — Linear and Binary Search; Bubble Sort and Insertion Sort
## Items File

Note: Topics 4.2 and 4.3 overlap in the 0478 syllabus. Topic 4.3 extends the algorithmic depth of 4.2 with more detailed analysis and pseudocode variants. This file provides extended practice items complementing 4.2.

**Item 1 [F]**
Question: What is meant by a "sorted list" in the context of search algorithms?
Answer: A sorted list has its elements arranged in a specific order — either ascending (smallest to largest) or descending (largest to smallest).
Difficulty: F
Topic: 4.3
Explanation: Binary search requires this property to eliminate half the remaining elements at each step. Linear search does not require sorting.
Tags: sorted list, ascending, descending, prerequisite

**Item 2 [F]**
Question: In a linear search of 100 names, what is the average number of comparisons if the target is present?
Answer: 50 comparisons.
Difficulty: F
Topic: 4.3
Explanation: On average, the target is in the middle of the list. So n/2 = 100/2 = 50 comparisons.
Tags: linear search, average case, comparisons

**Item 3 [F]**
Question: State one advantage of linear search over binary search.
Answer: Linear search works on unsorted lists without any pre-processing.
Difficulty: F
Topic: 4.3
Explanation: If data is unsorted and changes frequently, binary search's requirement to sort first (O(n log n)) may outweigh its search advantage.
Tags: linear search, advantage, unsorted data

**Item 4 [F]**
Question: What is the purpose of the `sorted` flag in bubble sort pseudocode?
Answer: It detects whether any swaps were made in the current pass. If no swaps occur, the list is already sorted and the algorithm can terminate early.
Difficulty: F
Topic: 4.3
Explanation: Initialise `sorted` to FALSE. After each pass, set `sorted` to TRUE. During comparisons, if a swap is made, set `sorted` to FALSE.
Tags: bubble sort, sorted flag, optimisation, early exit

**Item 5 [S]**
Question: What is the role of the "marker" or index pointer in insertion sort?
Answer: The marker indicates the first unsorted element. All elements to its left are guaranteed to be in sorted order.
Difficulty: S
Topic: 4.3
Explanation: Initially, marker = 1 (second element). Insert the marked element into its correct sorted position among the elements to its left.
Tags: insertion sort, marker, sorted portion, unsorted portion

**Item 6 [S]**
Question: Trace linear search on the list [12, 5, 8, 3, 20] looking for 8. Show the comparison count.
Answer: Check 12 (not match, count=1), check 5 (not match, count=2), check 8 (match, count=3). Found at index 2 with 3 comparisons.
Difficulty: S
Topic: 4.3
Explanation: Linear search checks each element in sequence from the start. For n=5, worst case is 5 comparisons.
Tags: linear search, trace, comparisons, found

**Item 7 [S]**
Question: Trace binary search on the sorted list [3, 7, 12, 15, 19, 23] looking for 15.
Answer: Step 1: mid = index 3 (value 15). Match found! Index = 3. Steps taken = 1.
Difficulty: S
Topic: 4.3
Explanation: first=0, last=5. mid=(0+5) DIV 2=3. list[3]=15 = target. Done in one comparison.
Tags: binary search, trace, sorted list, found

**Item 8 [S]**
Question: Trace binary search on the sorted list [3, 7, 12, 15, 19, 23] looking for 10.
Answer: Step 1: mid=3, value=15 > 10, search left: last=2. Step 2: mid=(0+2) DIV 2=1, value=7 < 10, search right: first=2. Step 3: mid=(2+2) DIV 2=2, value=12 > 10, search left: last=1. Now first=2 > last=1 → not found. Steps = 3.
Difficulty: S
Topic: 4.3
Explanation: The search space halves each time. When first exceeds last, the sublist is empty and the target is absent.
Tags: binary search, trace, not found, divide and conquer

**Item 9 [S]**
Question: Insert the value 6 into the sorted portion [2, 4, 7, 9] using insertion sort.
Answer: Starting from the right of the sorted portion: 9 > 6, shift right. 7 > 6, shift right. 4 ≤ 6, stop. Insert 6 between 4 and 7. Result: [2, 4, 6, 7, 9].
Difficulty: S
Topic: 4.3
Explanation: Each element to the right of the insertion point shifts one position right. The "hole" moves left until the correct position is found.
Tags: insertion sort, insertion, shift, sorted

**Item 10 [S]**
Question: How many passes does bubble sort make on a list of n items in the worst case?
Answer: n − 1 passes.
Difficulty: S
Topic: 4.3
Explanation: After n−1 passes, the n−1 largest elements are in their final positions. The nth element is then the smallest and in the correct position.
Tags: bubble sort, passes, worst case, n-1

**Item 11 [S]**
Question: Write pseudocode for bubble sort with an early-exit optimisation.
Answer: ```
REPEAT
  swapped ← FALSE
  FOR I ← 1 TO n − 1
    IF list[I−1] > list[I] THEN
      temp ← list[I−1]
      list[I−1] ← list[I]
      list[I] ← temp
      swapped ← TRUE
    ENDIF
  ENDFOR
UNTIL swapped = FALSE
```
Difficulty: S
Topic: 4.3
Explanation: If no swaps occur in a complete pass, the list is sorted and the REPEAT loop exits immediately, avoiding unnecessary passes.
Tags: bubble sort, pseudocode, swapped flag, optimisation

**Item 12 [S]**
Question: What is the space complexity of insertion sort?
Answer: O(1) — insertion sort sorts the list in place without needing additional data structures.
Difficulty: S
Topic: 4.3
Explanation: Only a constant amount of extra memory is used (for the temporary variable during swapping). This makes it suitable for memory-constrained environments.
Tags: insertion sort, space complexity, O(1), in-place

**Item 13 [C]**
Question: Write pseudocode for insertion sort.
Answer: ```
FOR I ← 1 TO n − 1
  j ← I
  WHILE j > 0 AND list[j−1] > list[j]
    temp ← list[j]
    list[j] ← list[j−1]
    list[j−1] ← temp
    j ← j − 1
  ENDWHILE
ENDFOR
```
Difficulty: C
Topic: 4.3
Explanation: The outer loop picks each element from index 1 onwards. The inner WHILE shifts larger elements one position right until the correct insertion spot is found.
Tags: insertion sort, pseudocode, implementation, inner loop

**Item 14 [C]**
Question: Compare the worst-case time complexity of insertion sort and bubble sort.
Answer: Both have O(n²) worst-case time complexity. However, bubble sort always makes n−1 passes, while insertion sort's inner loop may terminate early in best/average cases.
Difficulty: C
Topic: 4.3
Explanation: Worst case for both: reverse-sorted list. Bubble sort: n(n−1)/2 comparisons. Insertion sort: n(n−1)/2 comparisons (always shifts all sorted elements).
Tags: insertion sort, bubble sort, complexity, comparison

**Item 15 [C]**
Question: A list of 1000 integers is searched using binary search. What is the maximum number of comparisons needed?
Answer: 10 comparisons (log₂ 1000 ≈ 9.97, rounded up to 10).
Difficulty: C
Topic: 4.3
Explanation: log₂ 1000 ≈ 9.97. The ceiling of this is 10 comparisons. Each comparison halves the remaining list until the target is found or the list is empty.
Tags: binary search, log₂, maximum comparisons, ceiling

**Item 16 [C]**
Question: Show one complete pass of bubble sort on [4, 2, 7, 1], showing all swaps.
Answer: Compare (4,2): swap → [2, 4, 7, 1]. Compare (4,7): no swap → [2, 4, 7, 1]. Compare (7,1): swap → [2, 4, 1, 7]. Result after pass 1: [2, 4, 1, 7]. The largest value 7 has bubbled to the end.
Difficulty: C
Topic: 4.3
Explanation: Each pass places the next largest element in its final position. After pass 1, one element is in its correct position.
Tags: bubble sort, pass, swap, trace

**Item 17 [C]**
Question: Why might insertion sort be preferred over merge sort for small datasets?
Answer: Insertion sort has lower constant factors and less overhead. Merge sort requires O(n) extra space and recursive calls that are not worthwhile for small n.
Difficulty: C
Topic: 4.3
Explanation: For n < ~50, insertion sort is often faster in practice despite the same O(n²) theoretical complexity. Its in-place nature and simple loops are cache-friendly.
Tags: insertion sort, merge sort, small datasets, constant factors

**Item 18 [C]**
Question: For a sorted list of 1000 items, how many comparisons does binary search need in the best case and worst case?
Answer: Best case: 1 comparison (target is the middle element). Worst case: 10 comparisons (log₂ 1000 rounded up).
Difficulty: C
Topic: 4.3
Explanation: The worst case occurs when the target is at one end or absent. The number of comparisons equals the number of times you can halve 1000 before reaching a single element: ⌈log₂(1000)⌉ = 10.
Tags: binary search, best case, worst case, comparisons
