# Topic 4.2 — Searching and Sorting Algorithms
## Items File

**Item 1 [F]**
Question: State the two main categories of search algorithms covered in IGCSE Computer Science.
Answer: (1) Linear (sequential) search — checks each element in order. (2) Binary search — repeatedly halves a sorted list to find the target.
Difficulty: F
Topic: 4.2
Explanation: Linear search works on any list (sorted or unsorted). Binary search requires the list to be sorted first, but is much faster on large lists.
Tags: searching, algorithms, linear search, binary search

**Item 2 [F]**
Question: Describe the linear search algorithm.
Answer: Start from the first element. Compare each element with the target. If found, return the position. If the end of the list is reached without a match, report failure.
Difficulty: F
Topic: 4.2
Explanation: Linear search is straightforward but inefficient: on average it checks n/2 elements for a successful search and all n elements for an unsuccessful one.
Tags: linear search, sequential search, algorithm description

**Item 3 [F]**
Question: What is the maximum number of comparisons in a linear search of n items?
Answer: n comparisons (when the target is not found or is the last element).
Difficulty: F
Topic: 4.2
Explanation: In the worst case, linear search checks every element. Time complexity: O(n).
Tags: linear search, worst case, comparisons, complexity

**Item 4 [F]**
Question: What is the key requirement for binary search to work?
Answer: The list must be sorted in ascending (or descending) order.
Difficulty: F
Topic: 4.2
Explanation: Binary search works by repeatedly dividing the search space in half. If the list is unsorted, halving would give random results.
Tags: binary search, prerequisite, sorted list

**Item 5 [S]**
Question: Describe the binary search algorithm step by step.
Answer: (1) Find the middle element. (2) If it equals the target, found. (3) If target is smaller, search the left half. (4) If target is larger, search the right half. (5) Repeat until found or the sublist is empty.
Difficulty: S
Topic: 4.2
Explanation: Each step halves the remaining search space. For a list of n items, binary search takes at most log₂(n) steps.
Tags: binary search, algorithm steps, divide and conquer

**Item 6 [S]**
Question: How many comparisons does binary search make for a list of 128 items in the worst case?
Answer: 7 comparisons (log₂ 128 = 7).
Difficulty: S
Topic: 4.2
Explanation: Each comparison eliminates half of the remaining items. 128 → 64 → 32 → 16 → 8 → 4 → 2 → 1. After 7 comparisons, the list is reduced to one item.
Tags: binary search, log₂, comparisons, worst case

**Item 7 [S]**
Question: What is the time complexity of binary search?
Answer: O(log n) — logarithmic time. Each step halves the search space.
Difficulty: S
Topic: 4.2
Explanation: O(log n) means doubling the list size only adds one extra comparison. Much faster than O(n) linear search for large lists.
Tags: binary search, complexity, O(log n), time complexity

**Item 8 [S]**
Question: Describe the bubble sort algorithm.
Answer: Repeatedly step through the list, compare adjacent pairs, and swap them if they are in the wrong order. Repeat until no swaps are needed (list is sorted).
Difficulty: S
Topic: 4.2
Explanation: After each pass, the largest unsorted element "bubbles up" to its correct position. The algorithm terminates when a pass completes with no swaps.
Tags: bubble sort, sorting algorithm, swap, passes

**Item 9 [S]**
Question: What is the best-case time complexity of bubble sort?
Answer: O(n) — when the list is already sorted.
Difficulty: S
Topic: 4.2
Explanation: If no swaps are needed in the first pass, the algorithm terminates immediately. A flag is typically used to detect this.
Tags: bubble sort, best case, O(n), sorted list

**Item 10 [S]**
Question: What is the worst-case time complexity of bubble sort?
Answer: O(n²) — when the list is in reverse order.
Difficulty: S
Topic: 4.2
Explanation: In reverse order, every adjacent pair must be swapped. Each of the n passes makes up to n comparisons. Total: n × n = n².
Tags: bubble sort, worst case, O(n²), complexity

**Item 11 [S]**
Question: Describe the insertion sort algorithm.
Answer: For each element (starting from the second), compare it with elements before it and insert it into its correct sorted position in the left portion of the list.
Difficulty: S
Topic: 4.2
Explanation: Like sorting a hand of playing cards — pick up each card and place it in its correct position among the sorted cards already held.
Tags: insertion sort, sorting algorithm, insertion, partial sort

**Item 12 [S]**
Question: Compare the space complexity of linear search and binary search.
Answer: Both have O(1) space complexity — they sort the list in place and require only a constant amount of extra memory.
Difficulty: S
Topic: 4.2
Explanation: Neither algorithm requires additional data structures. The sorted list itself provides the search space.
Tags: space complexity, linear search, binary search, memory

**Item 13 [C]**
Question: Trace bubble sort on the list [5, 3, 8, 1] and show the state after each pass.
Answer: Pass 1: [3, 5, 1, 8]; Pass 2: [3, 1, 5, 8]; Pass 3: [1, 3, 5, 8]. Sorted after 3 passes.
Difficulty: C
Topic: 4.2
Explanation: Pass 1: (5,3)→swap, (5,8)→no swap, (8,1)→swap → [3,5,1,8]. Pass 2: (3,5)→no swap, (5,1)→swap → [3,1,5,8]. Pass 3: (3,1)→swap → [1,3,5,8]. No swaps in Pass 4 → sorted.
Tags: bubble sort, trace, step-by-step, pass

**Item 14 [C]**
Question: Write pseudocode for a linear search that returns the index of the target or −1 if not found.
Answer: ```
FUNCTION LinearSearch(list, target)
  FOR I ← 0 TO LENGTH(list) − 1
    IF list[I] = target THEN
      RETURN I
    ENDIF
  ENDFOR
  RETURN −1
ENDFUNCTION
```
Difficulty: C
Topic: 4.2
Explanation: Returns the first matching index. −1 is the sentinel value indicating failure, as 0 is a valid array index.
Tags: linear search, pseudocode, function, implementation

**Item 15 [C]**
Question: Write pseudocode for binary search on a sorted list.
Answer: ```
FUNCTION BinarySearch(list, target)
  first ← 0
  last ← LENGTH(list) − 1
  WHILE first ≤ last
    mid ← (first + last) DIV 2
    IF list[mid] = target THEN
      RETURN mid
    ELSEIF list[mid] > target THEN
      last ← mid − 1
    ELSE
      first ← mid + 1
    ENDIF
  ENDWHILE
  RETURN −1
ENDFUNCTION
```
Difficulty: C
Topic: 4.2
Explanation: Each iteration either finds the target, searches the left half, or searches the right half. The loop terminates when first > last (not found) or when the target is found.
Tags: binary search, pseudocode, function, implementation

**Item 16 [C]**
Question: Compare bubble sort and insertion sort in terms of efficiency for nearly-sorted data.
Answer: Insertion sort is more efficient for nearly-sorted data, achieving close to O(n) in best case. Bubble sort also achieves O(n) if a swap flag is used, but insertion sort typically performs fewer comparisons.
Difficulty: C
Topic: 4.2
Explanation: Nearly-sorted: insertion sort shifts elements only a few positions. Bubble sort still makes n passes but detects no swaps in early passes.
Tags: insertion sort, bubble sort, nearly sorted, comparison

**Item 17 [C]**
Question: State one advantage and one disadvantage of binary search over linear search.
Answer: Advantage: much faster on large lists (O(log n) vs O(n)). Disadvantage: requires the list to be sorted first.
Difficulty: C
Topic: 4.2
Explanation: Sorting takes O(n log n) time, so for small or infrequent searches, linear search may be preferable despite its higher per-search cost.
Tags: binary search, linear search, comparison, advantage, disadvantage

**Item 18 [C]**
Question: Why is the time complexity of O(n²) considered inefficient for large datasets?
Answer: O(n²) means the time grows with the square of the input size. Doubling the input quadruples the time. For n = 10,000, this means up to 100,000,000 operations.
Difficulty: C
Topic: 4.2
Explanation: O(n²) sorting algorithms (bubble, insertion) are acceptable for small lists (n < 100) but impractical for large datasets. For large n, O(n log n) algorithms (merge sort, quicksort) are preferred.
Tags: O(n²), time complexity, efficiency, sorting algorithms
