# Topic 6.3 — Data Validation and Verification
## Items File

**Item 1 [F]**
Question: What is the difference between data validation and data verification?
Answer: Validation checks whether data is sensible and within acceptable rules before accepting it. Verification checks whether data has been transcribed or entered correctly, typically by comparing it against a second source or entry.
Difficulty: F
Topic: 6.3
Explanation: Validation asks "is this data reasonable?" Verification asks "is this data correct?" Both are necessary for data quality, but they catch different types of errors.
Tags: validation, verification, definitions

**Item 2 [F]**
Question: What is a range check in data validation?
Answer: A range check verifies that a numeric value falls between a minimum and maximum acceptable value. For example, a mark must be between 0 and 100.
Difficulty: F
Topic: 6.3
Explanation: Range checks prevent obviously wrong values like negative marks or exam scores above the maximum possible. They are one of the most common validation rules.
Tags: validation rules, range check

**Item 3 [F]**
Question: What is the purpose of a presence check?
Answer: A presence check ensures that a required field is not left empty or blank. It prevents records from being saved without essential information.
Difficulty: F
Topic: 6.3
Explanation: Without a presence check, required fields like customer names or product codes could be accidentally omitted, creating incomplete and potentially unusable records.
Tags: validation rules, presence check

**Item 4 [F]**
Question: What is double entry verification?
Answer: Double entry requires the user to enter a value twice, such as when setting a password. The system checks that both entries match before accepting the data.
Difficulty: F
Topic: 6.3
Explanation: Double entry catches transcription errors by forcing an intentional repeat of the input. If the two entries differ, the user is prompted to re-enter the data.
Tags: verification, double entry, data entry errors

**Item 5 [F]**
Question: What does a length check validate?
Answer: A length check ensures that a text field contains a number of characters within a specified minimum and maximum. For example, a username must be between 3 and 20 characters.
Difficulty: F
Topic: 6.3
Explanation: Length checks prevent values that are too short to be meaningful or too long to fit in the database field. They also help prevent buffer overflow vulnerabilities in some systems.
Tags: validation rules, length check

**Item 6 [F]**
Question: State one common input error that data validation can detect and one that it cannot.
Answer: Validation can detect: a mark of 250 (outside the valid range of 0-100). Validation cannot detect: a correctly formatted but factually wrong answer (e.g., a valid date of birth that belongs to someone else).
Difficulty: F
Topic: 6.3
Explanation: Validation checks the format and reasonableness of data, not its truth. Only human review or cross-referencing against authoritative sources can catch factual errors.
Tags: validation rules, input errors, limitations

**Item 7 [S]**
Question: Explain the purpose of a check digit in a product barcode or ISBN number.
Answer: A check digit is a calculated extra digit appended to a number sequence. It is computed using a mathematical formula (such as the Luhn algorithm) applied to the other digits. When the number is entered, the system recalculates the check digit and compares it to the entered value. A mismatch indicates a transcription error.
Difficulty: S
Topic: 6.3
Explanation: Check digits detect common errors like mistyped digits or transposed numbers. They are used in barcodes, ISBN numbers, bank account numbers, and national ID numbers.
Tags: check digit, validation rules, error detection

**Item 8 [S]**
Question: Describe how a format check works and give an example of its use.
Answer: A format check uses a pattern or mask to verify that data matches an expected structure. For example, a UK postal code might be validated against the pattern AA9 9AA, where A represents a letter and 9 represents a digit. A telephone number might be checked against a pattern like +44-7XXX-XXXXXX.
Difficulty: S
Topic: 6.3
Explanation: Format checks use regular expressions or predefined masks to enforce structural correctness. They can catch transposition errors and missing digits that pass other validation rules.
Tags: validation rules, format check, pattern matching

**Item 9 [S]**
Question: Why is proofreading important as a verification technique for paper-based forms?
Answer: Proofreading involves a second person reading the entered data against the original paper form to spot transcription errors. A second pair of eyes can catch mistakes that the original data entry operator may have missed due to familiarity with the content.
Difficulty: S
Topic: 6.3
Explanation: Proofreading is a human verification technique. It catches errors that automated checks cannot, such as semantically wrong data that still passes format and range validation.
Tags: verification, proofreading, data entry

**Item 10 [S]**
Question: A type check is used on a field that should contain an integer. What would happen if the user entered "42.5"?
Answer: The type check would reject the input because "42.5" is a decimal number (floating-point), not an integer. The program would prompt the user to re-enter a whole number.
Difficulty: S
Topic: 6.3
Explanation: Type checks verify that the data type of the input matches the expected type. This prevents values that are technically in the wrong format from entering the system.
Tags: validation rules, type check, data types

**Item 11 [S]**
Question: What is the role of a verification technique in catching transposition errors?
Answer: Transposition errors occur when two digits are accidentally swapped (e.g., 1234 entered as 1243). Double entry verification catches these because the user must enter the value twice, and transposition will almost certainly differ between the two entries. Check digit schemes also detect many transposition errors through their mathematical formulas.
Difficulty: S
Topic: 6.3
Explanation: Transposition is one of the most common human data entry errors. Verification techniques are specifically designed to catch this class of mistake alongside omission and substitution errors.
Tags: verification, transposition errors, double entry

**Item 12 [S]**
Question: How does a format check differ from a type check?
Answer: A type check verifies the data type of a value (integer, string, date). A format check verifies the structure or pattern of the data (e.g., that a date follows DD/MM/YYYY format or that a postcode matches a specific pattern). A value can pass a type check but fail a format check.
Difficulty: S
Topic: 6.3
Explanation: For example, the string "25/13/2024" passes a type check (it is a string) but fails a format check (13 is not a valid month). Both checks are complementary and should be applied together.
Tags: validation rules, type check, format check

**Item 13 [C]**
Question: A hospital system records patient dates of birth. Design a set of validation rules for this field, explaining why each rule is necessary.
Answer: 1. Presence check — date of birth is mandatory for patient records. 2. Type check — must be a valid date type, not free text. 3. Format check — must follow a consistent pattern like DD/MM/YYYY. 4. Range check — date of birth must be in the past and within a plausible range (e.g., no one born before 1900 or after today's date). 5. Consistency check — the calculated age must be consistent with other records (e.g., a patient cannot have a procedure date before their date of birth). Together these rules prevent empty records, malformed dates, impossible dates, and logically inconsistent data.
Difficulty: C
Topic: 6.3
Explanation: Medical data requires especially rigorous validation because errors could lead to incorrect treatment. Multiple overlapping validation rules provide defence in depth against different types of input errors.
Tags: validation rules, range check, format check, consistency check

**Item 14 [C]**
Question: SQL constraints can be used to enforce validation rules at the database level. Explain how PRIMARY KEY, NOT NULL, CHECK, and UNIQUE constraints implement validation.
Answer: NOT NULL enforces a presence check by preventing the field from being empty. PRIMARY KEY combines NOT NULL and UNIQUE to ensure each record is uniquely identifiable with no duplicates. CHECK applies a specific condition — for example, CHECK (Age >= 0 AND Age <= 120) implements a range check. UNIQUE prevents duplicate values in non-primary fields. These constraints operate at the database level, meaning invalid data cannot enter the database through any application or direct query.
Difficulty: C
Topic: 6.3
Explanation: Database-level validation is more secure than application-level validation alone because it cannot be bypassed by a client application or direct SQL injection. It provides a final line of defence.
Tags: SQL, validation, constraints, database

**Item 15 [C]**
Question: Evaluate the effectiveness of check digit validation in preventing data entry errors, and identify its limitations.
Answer: Check digit validation is highly effective against common single-digit errors (detects roughly 100% of single-digit errors) and many transposition errors, depending on the algorithm used. It is computationally cheap and universally applicable to numeric codes. However, it has significant limitations. It cannot detect transposition of two non-adjacent digits in some schemes. It cannot detect errors where two different valid numbers are confused with each other. It detects but cannot correct errors. It is also ineffective against systematic errors (where the same mistake is made consistently) and most substitution-transposition combination errors.
Difficulty: C
Topic: 6.3
Explanation: No single validation technique catches all errors. Check digits are most effective as part of a layered validation strategy that includes format checks, range checks, and verification techniques like double entry.
Tags: check digit, validation, error detection, limitations

**Item 16 [C]**
Question: A retail website collects delivery addresses. Compare using client-side validation (in the web browser) versus server-side validation (on the web server) to ensure postcodes are correctly formatted.
Answer: Client-side validation provides immediate feedback to the user without waiting for a server round-trip, improving the user experience. However, it can be bypassed by disabling JavaScript or submitting requests directly, so it cannot be relied upon for security. Server-side validation is the authoritative check — it cannot be bypassed by the client and is the only place where validation can be trusted for security purposes such as preventing SQL injection. The best approach uses both: client-side validation for usability and server-side validation for security and data integrity.
Difficulty: C
Topic: 6.3
Explanation: This separation of concerns is a fundamental principle of web application design. Never trust data from the client; always re-validate on the server regardless of what client-side checks have been performed.
Tags: validation, client-side, server-side, web applications

**Item 17 [C]**
Question: Explain how validation and verification work together to ensure data quality in a new employee onboarding system, and describe scenarios where one technique would fail and the other would succeed.
Answer: Validation ensures each field meets format requirements: presence checks on required fields, format checks on email addresses and phone numbers, range checks on age (16-70), and type checks on dates. Verification ensures accurate transcription: double entry for bank account details, manual proofreading of entered data against original documents. Validation would fail to detect if an employee's name is misspelled from their original document — it passes every format and range check. Verification would catch this through proofreading or cross-referencing the original document. Conversely, verification cannot detect if an employee accidentally entered a valid-format but incorrect date of birth — it would pass double entry but the date itself would be wrong. Only the combination of both techniques achieves comprehensive data quality.
Difficulty: C
Topic: 6.3
Explanation: This demonstrates the complementary nature of the two approaches. Validation checks data against rules; verification checks data against source documents or a second entry. Both are necessary and neither is sufficient alone.
Tags: validation, verification, data quality, combined approach

**Item 18 [C]**
Question: Design a comprehensive validation strategy for an online examination system that awards marks between 0 and 100, including justification for each chosen rule.
Answer: 1. Presence check on all fields — ensures no incomplete submissions. 2. Type check on mark field — ensures numeric input, not text. 3. Range check (0 to 100) — enforces valid mark boundaries. 4. Format check on student ID — ensures consistent format like ABC123456. 5. Check digit on student ID — detects transposition and substitution errors in the ID. 6. Timestamp validation — ensures submission time is within the examination window. 7. Uniqueness check on student ID — prevents duplicate submissions. 8. Verification: double-entry of mark by second examiner for marks above 80 or below 30 (boundary values most prone to error). 9. Automated consistency check — total marks must equal sum of individual question marks. 10. Server-side re-validation of all rules regardless of client-side checks. The layered approach recognises that high-stakes academic data requires multiple overlapping checks because any single error could affect grade outcomes.
Difficulty: C
Topic: 6.3
Explanation: High-stakes systems require comprehensive validation because the cost of errors is high. Boundary values (0, 100) are particularly important to check explicitly because they are the most likely points of off-by-one errors.
Tags: validation strategy, range check, format check, verification, comprehensive design
