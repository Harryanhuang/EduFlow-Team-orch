# Topic 6.1 — Database Concepts
## QA Question Level File

**1. [F]** Define the following terms in the context of a database:
(a) Field
(b) Record
(c) Primary Key

**2. [F]** State the difference between a flat-file database and a relational database.

**3. [F]** What is a foreign key? Give an example of when it would be used.

**4. [S]** Describe two methods of data validation and explain why each is useful.

**5. [S]** Explain the difference between data validation and data verification. Give one example of each.

**6. [S]** What is a database index? State two advantages and one disadvantage of using an index on a field.

**7. [C]** A school database has three tables: `Students`, `Enrollments`, and `Courses`. `Enrollments` links students to courses using `StudentID` and `CourseID` as foreign keys.
(a) Explain why this relational structure is better than a single flat-file table storing all information.
(b) If a student is deleted from the `Students` table without handling the `Enrollments` table, what problem could occur?
(c) What is meant by cascade delete, and how would it solve the problem in part (b)?

**8. [C]** Explain what is meant by normalisation in database design. Describe the steps taken to normalise a database to third normal form (3NF), and explain why normalisation reduces data redundancy.

**9. [C]** A database table `Orders` has the fields: `OrderID`, `CustomerName`, `CustomerAddress`, `ProductName`, `Quantity`, `UnitPrice`, `TotalPrice`.
(a) Identify the problems that exist in this design.
(b) Show how you would decompose this into separate tables to achieve third normal form (3NF).
(c) Define what a database transaction is, and explain why ACID properties (Atomicity, Consistency, Isolation, Durability) are important when processing orders.
