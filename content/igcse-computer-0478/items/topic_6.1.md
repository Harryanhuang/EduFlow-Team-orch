# Topic 6.1 — Database Concepts
## Items File

**Item 1 [F]**
Question: What is a database?
Answer: A database is an organised collection of structured data stored electronically, allowing efficient storage, retrieval, and manipulation of information.
Difficulty: F
Topic: 6.1
Explanation: Databases replace paper filing systems. They allow fast search, update, and report generation. DBMS software manages the database.
Tags: database, definition, data management

**Item 2 [F]**
Question: Define: (a) field (b) record (c) primary key.
Answer: (a) Field: a single attribute of a record (e.g., Name, Age). (b) Record: a complete set of related fields about one entity (e.g., one student). (c) Primary key: a field that uniquely identifies each record (e.g., student number).
Difficulty: F
Topic: 6.1
Explanation: Field = column. Record = row. Primary key = unique identifier. Every record must have a unique primary key value.
Tags: field, record, primary key, database terminology

**Item 3 [F]**
Question: What is a flat-file database?
Answer: A flat-file database stores data in a single table, without relationships between tables. Each record is stored as one row.
Difficulty: F
Topic: 6.1
Explanation: Flat-file databases are simple but limited. Examples: spreadsheet, CSV file. They are suitable for small datasets but cause data duplication when storing related information.
Tags: flat-file, database, single table

**Item 4 [F]**
Question: State one advantage and one disadvantage of a flat-file database.
Answer: Advantage: simple to understand and implement. Disadvantage: data redundancy (duplication) when the same data appears in multiple records.
Difficulty: F
Topic: 6.1
Explanation: Flat-files are easy to set up in a spreadsheet. Redundancy leads to update anomalies — changing a student's address requires updating every occurrence.
Tags: flat-file, advantages, disadvantages, data redundancy

**Item 5 [S]**
Question: What is a relational database?
Answer: A relational database stores data in multiple related tables. Tables are linked by common fields (foreign keys), reducing data redundancy.
Difficulty: S
Topic: 6.1
Explanation: Relational databases use keys to connect tables: primary key in one table is the foreign key in another. This normalisation eliminates duplication.
Tags: relational database, tables, normalisation, foreign key

**Item 6 [S]**
Question: What is a foreign key?
Answer: A foreign key is a field in one table that links to the primary key of another table, establishing a relationship between them.
Difficulty: S
Topic: 6.1
Explanation: Example: ORDER table has CustomerID as foreign key linking to CUSTOMER table's primary key. Foreign keys enforce referential integrity — a DBMS rejects orders for non-existent customers.
Tags: foreign key, primary key, relationship, referential integrity

**Item 7 [S]**
Question: What is data validation?
Answer: Data validation checks that input data is reasonable and in the correct format before accepting it. It prevents invalid data entering the database.
Difficulty: S
Topic: 6.1
Explanation: Validation types: presence check (is the field empty?), range check (age 0–150), type check (number vs text), format check (email has @ symbol), length check.
Tags: data validation, input checking, data quality

**Item 8 [S]**
Question: State three types of data validation.
Answer: (1) Presence check — field is not empty. (2) Range check — number within minimum and maximum values. (3) Type check — correct data type entered.
Difficulty: S
Topic: 6.1
Explanation: Format check (postcode pattern), length check (password 8+ chars), lookup check (country from a list of valid countries).
Tags: validation types, data entry, input checking

**Item 9 [S]**
Question: What is data verification?
Answer: Data verification checks that data has been entered correctly by comparing two independent copies or re-entering and checking for differences.
Difficulty: S
Topic: 6.1
Explanation: Verification ensures no transcription errors. Example: typing a password twice and checking they match. Verification does not detect the original error, only transcription mistakes.
Tags: data verification, double-entry, accuracy, transcription

**Item 10 [S]**
Question: What is normalisation?
Answer: Normalisation organises data into related tables to reduce redundancy and improve data integrity.
Difficulty: S
Topic: 6.1
Explanation: Normalisation splits large tables into smaller, related tables. First Normal Form (1NF): atomic values, no repeating groups. Second Normal Form (2NF): no partial dependencies. Third Normal Form (3NF): no transitive dependencies.
Tags: normalisation, database design, redundancy, 1NF, 2NF, 3NF

**Item 11 [S]**
Question: What is the purpose of an index in a database?
Answer: An index speeds up searching and sorting on a field. The index is a separate structure pointing to records by primary key value.
Difficulty: S
Topic: 6.1
Explanation: Without an index, finding a record requires a full table scan. An index on Name allows direct access. Drawback: indices slow down updates and consume storage space.
Tags: index, searching, database optimisation, efficiency

**Item 12 [S]**
Question: State two advantages of using a database over paper filing.
Answer: (1) Speed: instant search and retrieval vs manual searching. (2) Data integrity: validation rules prevent inconsistent data. (3) Multiple simultaneous users. (4) Security: access controls and permissions.
Difficulty: S
Topic: 6.1
Explanation: Database advantages include backup/restore, concurrent access, query language (SQL), and security controls that paper files cannot provide.
Tags: database, advantages, file system comparison, efficiency

**Item 13 [S]**
Question: What is a transaction in a database?
Answer: A transaction is a sequence of operations treated as a single unit. All operations succeed or all are rolled back if any fails (atomicity).
Difficulty: S
Topic: 6.1
Explanation: Example: bank transfer (debit one account, credit another). Either both happen or neither happens. Transactions ensure consistency — the database is never left in a half-changed state.
Tags: transaction, atomicity, rollback, ACID, commit

**Item 14 [S]**
Question: What is a cascade delete?
Answer: Cascade delete automatically removes related records when a parent record is deleted. If a customer is deleted, cascade delete removes all their orders.
Difficulty: S
Topic: 6.1
Explanation: Cascade delete is a referential integrity action. Without cascade, deleting a parent record would leave orphaned child records (orders with no customer). The database enforces the relationship.
Tags: cascade delete, referential integrity, foreign key, parent-child

**Item 15 [S]**
Question: What is the difference between data and information?
Answer: Data is raw facts and figures (e.g., numbers, text). Information is data that has been processed and presented in context (e.g., a report showing monthly sales).
Difficulty: S
Topic: 6.1
Explanation: Data becomes information when organised, summarised, or analysed. The database stores data; reports present information.
Tags: data vs information, knowledge hierarchy, processing

**Item 16 [C]**
Question: A school database has tables STUDENT (StudentID PK, Name, TutorGroupID FK) and TUTOR (TutorID PK, TutorName, Room). Explain why TutorGroupID in STUDENT references TutorID in TUTOR.
Answer: TutorGroupID in STUDENT is a foreign key linking to the primary key TutorID in TUTOR. This enforces referential integrity: every student must belong to a valid tutor group.
Difficulty: C
Topic: 6.1
Explanation: The foreign key constraint prevents assigning a student to a non-existent tutor group. When a tutor is deleted, cascade delete can remove all their students if configured.
Tags: foreign key, primary key, referential integrity, normalisation

**Item 17 [C]**
Question: Design a normalised database for a library with books and authors.
Answer: Three tables: BOOK (BookID PK, Title, AuthorID FK), AUTHOR (AuthorID PK, Name), BOOK_AUTHOR (BookID FK, AuthorID FK — composite primary key). BOOK links to AUTHOR via BOOK_AUTHOR. This prevents duplicate author names and allows many-to-many relationships (one book by many authors, one author of many books).
Difficulty: C
Topic: 6.1
Explanation: A book can have multiple authors and an author can write multiple books. This many-to-many relationship requires a junction table (BOOK_AUTHOR). normalisation eliminates the redundancy of storing author names in the BOOK table.
Tags: normalisation, many-to-many, junction table, database design
