# Topic 5.4 — File Handling
## Items File

**Item 1 [F]**
Question: What is a file in the context of programming?
Answer: A file is a named collection of data stored on secondary storage (hard disk, SSD, USB drive), which persists after the program ends.
Difficulty: F
Topic: 5.4
Explanation: Unlike variables (which are lost when the program ends), files allow data to be saved and retrieved later.
Tags: file, secondary storage, data persistence

**Item 2 [F]**
Question: State two types of file access methods.
Answer: (1) Sequential access — data is read/written in order, from the beginning. (2) Random (direct) access — data is read/written at any location directly using a record number.
Difficulty: F
Topic: 5.4
Explanation: Sequential access is like a tape; random access is like a CD where any track can be accessed directly.
Tags: sequential access, random access, direct access, file access

**Item 3 [F]**
Question: What is the difference between a text file and a binary file?
Answer: A text file stores data as human-readable characters (ASCII or Unicode). A binary file stores data in its raw binary form, readable only by programs.
Difficulty: F
Topic: 5.4
Explanation: Text files: .txt, .csv, .html. Binary files: .exe, .jpg, .mp3. Text files can be opened in any text editor; binary files cannot.
Tags: text file, binary file, file types, ASCII

**Item 4 [F]**
Question: What does it mean to "open" a file in programming?
Answer: Opening a file establishes a connection between the program and the file on disk, allowing data to be read from or written to it.
Difficulty: F
Topic: 5.4
Explanation: Before reading or writing, a file must be opened. The operating system allocates resources to manage the file connection.
Tags: file open, OPEN, file handle

**Item 5 [S]**
Question: What does the statement OPENFILE "data.txt" FOR READ do?
Answer: It opens the file "data.txt" in read mode, allowing the program to read data from it. Writing to the file is not permitted in this mode.
Difficulty: S
Topic: 5.4
Explanation: After opening for READ, the READFILE command is used to retrieve data.
Tags: OPENFILE, READ mode, file opening

**Item 6 [S]**
Question: What does the statement OPENFILE "log.txt" FOR WRITE do?
Answer: It opens the file "log.txt" in write mode. If the file already exists, its contents are erased. New data written replaces the existing content.
Difficulty: S
Topic: 5.4
Explanation: Write mode creates a fresh file. Use APPEND mode if you want to add to existing content.
Tags: OPENFILE, WRITE mode, file writing, overwrite

**Item 7 [S]**
Question: What is the difference between WRITE and APPEND modes when opening a file?
Answer: WRITE mode erases the existing content and starts from the beginning. APPEND mode adds new data to the end of the existing file.
Difficulty: S
Topic: 5.4
Explanation: Use WRITE for creating new files or replacing content. Use APPEND for adding log entries without losing existing data.
Tags: APPEND mode, WRITE mode, file modes

**Item 8 [S]**
Question: Write pseudocode to open a file for reading and read all records until the end.
Answer: ```
OPENFILE "students.txt" FOR READ
WHILE NOT EOF
  READFILE "students.txt", record
  OUTPUT record
ENDWHILE
CLOSEFILE "students.txt"
```
Difficulty: S
Topic: 5.4
Explanation: EOF (End Of File) is a special marker that signals when there is no more data to read.
Tags: READFILE, EOF, file reading, loop

**Item 9 [S]**
Question: What does EOF stand for and what is its purpose?
Answer: End Of File. It is a flag that is TRUE when the end of the file has been reached, allowing the reading loop to terminate correctly.
Difficulty: S
Topic: 5.4
Explanation: Attempting to READ past EOF causes an error. The program must check EOF before each read.
Tags: EOF, end of file, file reading, loop termination

**Item 10 [S]**
Question: What does CLOSEFILE do and why is it important?
Answer: CLOSEFILE closes the file connection and releases the resources used by the operating system. It ensures all data is saved and prevents file corruption.
Difficulty: S
Topic: 5.4
Explanation: Always close files after use. If a program crashes before closing a file, data may be lost or the file may be corrupted.
Tags: CLOSEFILE, file closing, resource management

**Item 11 [S]**
Question: What is a CSV file? Give one example of its use.
Answer: CSV (Comma-Separated Values) is a text file where each record is on a line and fields are separated by commas. Example: student data (name, age, score) saved as "Alice,15,95".
Difficulty: S
Topic: 5.4
Explanation: CSV files are plain text, portable, and can be opened in spreadsheets like Excel.
Tags: CSV file, comma-separated, text file, data exchange

**Item 12 [S]**
Question: State one advantage of using a file over storing data in variables.
Answer: Data in files persists after the program ends — it can be loaded and used by the program in future sessions.
Difficulty: S
Topic: 5.4
Explanation: Variables are lost when the program terminates. Files enable long-term data storage and data sharing between programs.
Tags: file advantage, data persistence, secondary storage

**Item 13 [C]**
Question: Write pseudocode to create a new file and write three student names to it.
Answer: ```
OPENFILE "names.txt" FOR WRITE
WRITEFILE "names.txt", "Alice"
WRITEFILE "names.txt", "Bob"
WRITEFILE "names.txt", "Charlie"
CLOSEFILE "names.txt"
```
Difficulty: C
Topic: 5.4
Explanation: Each WRITEFILE call writes one line to the file. The file must be opened in WRITE mode before writing.
Tags: WRITEFILE, file creation, WRITE mode, pseudocode

**Item 14 [C]**
Question: Explain what happens if you try to OPENFILE for READ a file that does not exist.
Answer: An error occurs — the program cannot open a file that does not exist in READ mode. The program should check whether the file exists before attempting to open it.
Difficulty: C
Topic: 5.4
Explanation: Before opening for READ, the program should check: IF EXISTS("filename") THEN OPENFILE... This prevents runtime errors.
Tags: file not found, error handling, EXISTS, OPENFILE

**Item 15 [C]**
Question: Write pseudocode to count the number of records in a text file.
Answer: ```
OPENFILE "data.txt" FOR READ
count ← 0
WHILE NOT EOF
  READFILE "data.txt", record
  count ← count + 1
ENDWHILE
CLOSEFILE "data.txt"
OUTPUT count
```
Difficulty: C
Topic: 5.4
Explanation: Each iteration reads one record and increments the counter. When EOF is reached, the loop exits and the total count is output.
Tags: file reading, record counting, EOF, loop

**Item 16 [C]**
Question: What is the purpose of a file buffer?
Answer: A file buffer temporarily holds data before it is written to or read from the file, reducing the number of disk access operations.
Difficulty: C
Topic: 5.4
Explanation: Writing one byte at a time to disk is slow. The buffer accumulates data and writes it in larger blocks, improving performance. The CLOSEFILE ensures the buffer is flushed.
Tags: file buffer, performance, disk access, buffering

**Item 17 [C]**
Question: Write pseudocode to search for a specific name in a file and output whether it was found.
Answer: ```
OPENFILE "names.txt" FOR READ
found ← FALSE
WHILE NOT EOF AND found = FALSE
  READFILE "names.txt", name
  IF name = target THEN
    found ← TRUE
  ENDIF
ENDWHILE
CLOSEFILE "names.txt"
IF found THEN OUTPUT "Found" ELSE OUTPUT "Not found"
```
Difficulty: C
Topic: 5.4
Explanation: Combines file reading with a linear search. The loop stops early if the target is found, avoiding unnecessary reads.
Tags: file search, linear search, EOF, conditional

**Item 18 [C]**
Question: What is the difference between sequential access and random access files? Which is faster for finding a specific record?
Answer: Sequential: read records one by one from the start. Random: go directly to a specific record using its number. Random access is faster for finding specific records because it does not need to read preceding records.
Difficulty: C
Topic: 5.4
Explanation: Random access requires that each record is the same fixed length, so the file address can be calculated: address = (record_number − 1) × record_length.
Tags: sequential access, random access, direct access, file organisation
