# Topic 5.5 — File Handling (Extended)
## Items File

**Item 1 [F]**
Question: What is meant by a "fixed-length record" in file handling?
Answer: A fixed-length record is a data structure where every record occupies the same number of bytes. Each field within the record also has a predetermined size.
Difficulty: F
Topic: 5.5
Explanation: Because every record is the same size, the file can calculate the exact byte offset for any record using the formula: offset = record number multiplied by record length. This enables direct access to any record without reading from the beginning.
Tags: fixed-length records, file structure, record

**Item 2 [F]**
Question: Name three file open modes and describe what each allows.
Answer: Read mode allows data to be read from the file but not modified. Write mode creates a new file or overwrites an existing one, discarding previous content. Append mode allows new data to be added to the end of an existing file without altering existing records.
Difficulty: F
Topic: 5.5
Explanation: Choosing the correct mode is essential. Opening in write mode when intending to read will destroy data. Opening in read mode when the file does not exist will cause an error.
Tags: file open modes, read, write, append

**Item 3 [F]**
Question: What is a CSV file and what does CSV stand for?
Answer: CSV stands for Comma-Separated Values. It is a text file format where each record is on a new line and fields within a record are separated by commas.
Difficulty: F
Topic: 5.5
Explanation: CSV files are commonly used for exchanging data between applications because they are plain text and can be opened in any spreadsheet program or text editor.
Tags: CSV, file format, data exchange

**Item 4 [F]**
Question: Why is error handling important when opening a file for reading?
Answer: If the file does not exist, attempting to open it will cause a runtime error that could crash the program. Proper error handling prevents this by checking whether the file exists first or catching the error gracefully.
Difficulty: F
Topic: 5.5
Explanation: File not found errors are among the most common runtime errors. A robust program should inform the user and offer alternatives rather than crashing.
Tags: error handling, file not found, robust code

**Item 5 [F]**
Question: What is the difference between a text file and a binary file?
Answer: A text file stores data as human-readable characters using encoding schemes like ASCII or UTF-8. A binary file stores data in its raw binary form, which may represent numbers, images, or other data types that are not meant to be read as plain text.
Difficulty: F
Topic: 5.5
Explanation: Opening a binary file in a text editor produces garbled characters because the byte values do not correspond to printable characters. Binary files require special programs to interpret their structure.
Tags: binary files, text files, file types

**Item 6 [F]**
Question: What does "random access" mean in the context of file handling?
Answer: Random access means that any record in the file can be read or written directly without having to start from the beginning and read through all preceding records.
Difficulty: F
Topic: 5.5
Explanation: Random access is possible when records are fixed-length because the exact byte position of any record can be calculated using its index. This contrasts with sequential access, where records must be read in order.
Tags: random access, sequential access, fixed-length records

**Item 7 [S]**
Question: A file contains fixed-length records of 80 bytes each. Calculate the byte offset needed to read the 25th record.
Answer: Offset = (25 - 1) × 80 = 1,920 bytes from the start of the file.
Difficulty: S
Topic: 5.5
Explanation: Record numbers in random access typically start at 0 or 1. Subtracting 1 from the record number gives the zero-based index. Multiplying by the record length gives the byte offset.
Tags: random access, fixed-length records, offset calculation

**Item 8 [S]**
Question: Describe the process a program follows to validate data read from a CSV file before processing it.
Answer: The program should check each field for the correct data type, verify that required fields are not empty (presence check), confirm that values fall within acceptable ranges, check that string lengths do not exceed field limits, and validate format patterns where applicable. Any record failing validation should be logged and either skipped or reported to the user.
Difficulty: S
Topic: 5.5
Explanation: CSV data comes from external sources and cannot be trusted. Validating at the point of import prevents corrupted or malformed data from propagating into the application.
Tags: CSV, data validation, file handling

**Item 9 [S]**
Question: Write pseudocode to open a file for reading and handle the case where the file does not exist.
Answer: TRY
  OPENFILE "data.txt" FOR READ
  // process file contents
  CLOSEFILE
CATCH FileNotFoundError
  OUTPUT "Error: The file could not be found. Please check the filename."
ENDTRY
Difficulty: S
Topic: 5.5
Explanation: Exception handling ensures the program does not crash and provides meaningful feedback to the user. The TRY...CATCH block isolates the error-prone code.
Tags: error handling, file not found, pseudocode

**Item 10 [S]**
Question: Explain why random access is not suitable for CSV files.
Answer: CSV files store records of varying length because fields contain commas of different sizes. This means the byte offset of any record cannot be calculated without reading from the start of the file. Records must be accessed sequentially, line by line.
Difficulty: S
Topic: 5.5
Explanation: CSV files are inherently sequential. Random access requires fixed-length records, which is why database files and binary files use fixed-length structures to support direct access.
Tags: random access, CSV, sequential access, file types

**Item 11 [S]**
Question: A program needs to add a new record to the end of an existing file. Which file open mode should be used and why?
Answer: Append mode should be used. This mode positions the file pointer at the end of the file so that new data is written after all existing records without modifying any existing content.
Difficulty: S
Topic: 5.5
Explanation: Opening in write mode would erase the existing file. Opening in read mode would not allow writing. Append mode is specifically designed for this use case.
Tags: file open modes, append mode, writing

**Item 12 [S]**
Question: What are the advantages of using fixed-length records over variable-length records in a file?
Answer: Fixed-length records allow random access by calculating byte offsets directly. They also simplify searching and sorting because record boundaries are predictable. They reduce the complexity of code that inserts or deletes records.
Difficulty: S
Topic: 5.5
Explanation: The trade-off is potential waste — a fixed-length record always allocates the maximum possible space, even if the actual data is shorter than the maximum.
Tags: fixed-length records, random access, advantages

**Item 13 [C]**
Question: Design a file structure for a student records system where each record contains student ID (8 characters), name (40 characters), and exam mark (integer). Explain how random access would be used to retrieve a specific student record.
Answer: Each record occupies 8 + 40 + 4 = 52 bytes. The Student ID field occupies bytes 0-7, Name occupies bytes 8-47, and Exam Mark occupies bytes 48-51. To retrieve record number N (zero-indexed), calculate offset = N × 52, seek to that byte position, then read exactly 52 bytes and parse each field according to its defined position. This allows instant retrieval of any record without scanning preceding records.
Difficulty: C
Topic: 5.5
Explanation: The design assumes all strings are padded with spaces to their maximum length. This padding is what makes records fixed-length and enables direct byte-offset calculation.
Tags: fixed-length records, random access, file design

**Item 14 [C]**
Question: A logistics company stores delivery records in a binary file. Compare this approach with storing the same records in a CSV text file, focusing on storage efficiency, ease of debugging, and interoperability.
Answer: Binary storage is more space-efficient — a 4-byte integer occupies 4 bytes instead of up to 11 characters in decimal text. However, binary files cannot be read in a text editor and are difficult to debug manually. CSV files are human-readable, can be inspected and edited with any text editor or spreadsheet, and can be exchanged between different software systems without compatibility issues. For debugging and data exchange, CSV is superior. For high-volume storage and fast processing, binary is superior.
Difficulty: C
Topic: 5.5
Explanation: The choice involves trade-offs between efficiency and accessibility. Binary files also require knowledge of the exact structure to decode correctly, whereas CSV is self-describing.
Tags: binary files, CSV, storage efficiency, interoperability

**Item 15 [C]**
Question: Write pseudocode to process a CSV file containing student records with fields for name and mark, validating that the mark is between 0 and 100, and counting how many records pass and fail validation.
Answer: PassCount = 0
FailCount = 0
OPENFILE "students.csv" FOR READ
WHILE NOT EOF
  READLINE Line
  Split Line by "," into Fields
  Name = Fields[0]
  Mark = CONVERT_TO_INTEGER(Fields[1])
  IF Mark >= 0 AND Mark <= 100 THEN
    PassCount = PassCount + 1
  ELSE
    FailCount = FailCount + 1
    OUTPUT "Invalid mark for " + Name + ": " + Fields[1]
  ENDIF
ENDWHILE
CLOSEFILE
OUTPUT "Valid: " + PassCount + ", Invalid: " + FailCount
Difficulty: C
Topic: 5.5
Explanation: This demonstrates validation at import time. Each record is checked before being counted. Invalid records do not stop processing but are logged so they can be corrected.
Tags: CSV, file handling, validation, pseudocode

**Item 16 [C]**
Question: A database file uses fixed-length records and supports both sequential access (for reports) and random access (for lookups). Explain how these two access methods would be implemented and where each would be preferred.
Answer: Sequential access reads records in order from byte 0, incrementing the pointer by the record length each time. It is preferred when generating reports, printing all records, or performing batch operations. Random access calculates the byte offset as record_number × record_length, seeks directly to that position, and reads one record. It is preferred for instant lookups by record number, such as retrieving a specific customer or updating a known record. The underlying file structure supports both without modification.
Difficulty: C
Topic: 5.5
Explanation: The fixed-length record design enables both access patterns from the same file. This dual capability is a key advantage of the fixed-length approach over variable-length alternatives.
Tags: random access, sequential access, fixed-length records

**Item 17 [C]**
Question: A program must modify a record in the middle of a fixed-length record file. Explain why writing the updated record immediately to its original position is safe, but doing the same in a CSV file would be problematic.
Answer: In a fixed-length record file, writing 52 bytes at offset 1564 replaces exactly those 52 bytes without affecting adjacent records. Each record occupies a precise, known byte range. In a CSV file, records vary in length, so the replacement record may be longer or shorter than the original. Overwriting with a longer record would corrupt the next record, and writing a shorter record would leave orphaned characters. To modify a CSV record safely, the entire file must be rewritten.
Difficulty: C
Topic: 5.5
Explanation: This demonstrates why random-access file updates require fixed-length records. The predictability of each record's size is what makes in-place modification safe.
Tags: fixed-length records, CSV, file modification, random access

**Item 18 [C]**
Question: Evaluate the statement: "Binary files are always better than text files for storing application data."
Answer: The statement is false. Binary files offer superior storage efficiency and faster read/write operations for numeric data, but they sacrifice human readability, cross-platform compatibility, and ease of debugging. A text file can be opened in any editor, checked by scripts, and validated without special tools. A binary file requires exact knowledge of its structure to interpret correctly. For configuration files, data exchange, and debugging purposes, text formats like CSV or JSON are far superior. For high-performance internal storage of large numeric datasets, binary files are better. The choice depends on the use case: interchange and debugging favour text; performance and compactness favour binary.
Difficulty: C
Topic: 5.5
Explanation: The binary-versus-text debate is a classic trade-off in software engineering. Modern applications often use structured text formats like JSON or XML that combine some human readability with organised data representation.
Tags: binary files, text files, evaluation, file design
