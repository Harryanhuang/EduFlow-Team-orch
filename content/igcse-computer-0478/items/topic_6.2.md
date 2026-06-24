# Topic 6.2 — SQL Queries
## Items File

**Item 1 [F]**
Question: What does SQL stand for and what is it used for?
Answer: Structured Query Language. SQL is used to communicate with, retrieve, and manipulate data in relational databases.
Difficulty: F
Topic: 6.2
Explanation: SQL is the standard language for relational databases. It allows users to create tables, insert data, query specific information, and modify records.
Tags: SQL, database, query, definition

**Item 2 [F]**
Question: Write an SQL query to select all fields from a table called STUDENTS.
Answer: SELECT * FROM STUDENTS;
Difficulty: F
Topic: 6.2
Explanation: SELECT * means select all columns. FROM specifies the table. The semicolon ends the statement.
Tags: SQL, SELECT, all fields, query

**Item 3 [F]**
Question: What is the purpose of the WHERE clause in SQL?
Answer: WHERE filters records based on a specified condition, so only rows matching the condition are returned.
Difficulty: F
Topic: 6.2
Explanation: Example: SELECT * FROM STUDENTS WHERE Age > 15; returns only students older than 15.
Tags: WHERE, SQL, filtering, condition

**Item 4 [F]**
Question: Write an SQL query to select the Name and Age columns from STUDENTS where Age is greater than 15.
Answer: SELECT Name, Age FROM STUDENTS WHERE Age > 15;
Difficulty: F
Topic: 6.2
Explanation: Column names follow SELECT, separated by commas. The WHERE clause filters rows.
Tags: SQL, SELECT specific columns, WHERE, query

**Item 5 [S]**
Question: What is the difference between ORDER BY ASC and ORDER BY DESC?
Answer: ASC sorts in ascending order (smallest to largest, A to Z). DESC sorts in descending order (largest to smallest, Z to A).
Difficulty: S
Topic: 6.2
Explanation: Example: SELECT * FROM STUDENTS ORDER BY Age ASC; lists youngest first. ORDER BY Age DESC; lists oldest first.
Tags: ORDER BY, ASC, DESC, sorting

**Item 6 [S]**
Question: Write an SQL query to select all students ordered by Name in alphabetical order.
Answer: SELECT * FROM STUDENTS ORDER BY Name ASC;
Difficulty: S
Topic: 6.2
Explanation: Ordering by a text column arranges strings alphabetically. ASC is the default sort order.
Tags: ORDER BY, alphabetical, string sorting

**Item 7 [S]**
Question: What is the purpose of the DISTINCT keyword in SQL?
Answer: DISTINCT removes duplicate values from the result set, returning only unique values.
Difficulty: S
Topic: 6.2
Explanation: SELECT DISTINCT Country FROM STUDENTS; returns each country only once, even if multiple students are from the same country.
Tags: DISTINCT, duplicates, SQL, query

**Item 8 [S]**
Question: Write an SQL query to count the total number of records in the STUDENTS table.
Answer: SELECT COUNT(*) FROM STUDENTS;
Difficulty: S
Topic: 6.2
Explanation: COUNT(*) counts all rows including those with NULL values. COUNT(column) counts non-NULL values in that column.
Tags: COUNT, aggregate function, SQL, total records

**Item 9 [S]**
Question: Write an SQL query to find the average Age of all students.
Answer: SELECT AVG(Age) FROM STUDENTS;
Difficulty: S
Topic: 6.2
Explanation: AVG() is an aggregate function that calculates the mean of the specified column.
Tags: AVG, aggregate function, SQL, average

**Item 10 [S]**
Question: What is the purpose of the LIKE operator in SQL?
Answer: LIKE is used in WHERE clauses to search for a specified pattern in a column. Wildcards (%) and (_) are used to match multiple characters.
Difficulty: S
Topic: 6.2
Explanation: SELECT * FROM STUDENTS WHERE Name LIKE 'A%'; returns all names starting with A. % matches any sequence of characters.
Tags: LIKE, pattern matching, wildcard, SQL

**Item 11 [S]**
Question: Write an SQL query to find all students whose name starts with the letter "J".
Answer: SELECT * FROM STUDENTS WHERE Name LIKE 'J%';
Difficulty: S
Topic: 6.2
Explanation: 'J%' means J followed by any sequence of characters. 'J%' would match John, James, Jane, etc.
Tags: LIKE, wildcard, pattern, WHERE

**Item 12 [S]**
Question: What is a primary key in the context of an SQL database?
Answer: A primary key is a column (or set of columns) that uniquely identifies each record in a table. No two rows can have the same primary key value.
Difficulty: S
Topic: 6.2
Explanation: In a STUDENTS table, StudentID would be the primary key. Each student has a unique ID.
Tags: primary key, unique identifier, table, SQL

**Item 13 [C]**
Question: Write an SQL query to select students aged 16 or older, ordered by Age from oldest to youngest.
Answer: SELECT * FROM STUDENTS WHERE Age >= 16 ORDER BY Age DESC;
Difficulty: C
Topic: 6.2
Explanation: WHERE Age >= 16 filters the rows. ORDER BY Age DESC sorts in descending (largest to smallest) order.
Tags: WHERE, ORDER BY, DESC, combined query

**Item 14 [C]**
Question: Write an SQL query to find the maximum and minimum scores from a table called RESULTS.
Answer: SELECT MAX(Score), MIN(Score) FROM RESULTS;
Difficulty: C
Topic: 6.2
Explanation: MAX() and MIN() return the largest and smallest values respectively in the specified column.
Tags: MAX, MIN, aggregate functions, SQL

**Item 15 [C]**
Question: What is the purpose of GROUP BY in SQL? Give an example.
Answer: GROUP BY groups rows with the same value in a column so that aggregate functions can be applied to each group.
Difficulty: C
Topic: 6.2
Explanation: SELECT Country, COUNT(*) FROM STUDENTS GROUP BY Country; counts how many students are in each country.
Tags: GROUP BY, aggregate, grouping, SQL

**Item 16 [C]**
Question: Write an SQL query to list the number of students in each country.
Answer: SELECT Country, COUNT(*) FROM STUDENTS GROUP BY Country;
Difficulty: C
Topic: 6.2
Explanation: GROUP BY Country groups all students by their country. COUNT(*) then counts how many are in each group.
Tags: GROUP BY, COUNT, SQL query, grouping

**Item 17 [C]**
Question: What is a foreign key in SQL? Give an example.
Answer: A foreign key is a column in one table that references the primary key of another table, establishing a relationship between them.
Difficulty: C
Topic: 6.2
Explanation: In an ORDERS table, CustomerID is a foreign key that references the CustomerID primary key in the CUSTOMERS table.
Tags: foreign key, primary key, relationship, normalisation

**Item 18 [C]**
Question: Write an SQL query to find students whose names contain the letter "a" (case-insensitive) and have an Age between 14 and 16.
Answer: SELECT * FROM STUDENTS WHERE Name LIKE '%a%' AND Age BETWEEN 14 AND 16;
Difficulty: C
Topic: 6.2
Explanation: LIKE '%a%' matches any name containing 'a'. BETWEEN 14 AND 16 is inclusive on both ends, equivalent to Age >= 14 AND Age <= 16.
Tags: LIKE, BETWEEN, AND, combined WHERE, SQL
