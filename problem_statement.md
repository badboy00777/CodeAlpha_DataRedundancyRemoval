# Problem Statement: Data Redundancy Removal System

 CodeAlpha Cloud Computing Internship, Task 1

## 1. Task 
1. Design a system that identifies and classifies data as redundant or false positive.
2. Implement a validation mechanism to check new data against existing data.
3. Prevent duplicate data from being added into the cloud database.
4. Append only unique and verified data entries to the database.
5. Ensure database accuracy and efficiency by removing or avoiding redundancy.

## 2. Our interpretation
- **Data:** customer contact records (`full_name`, `email`, `phone`, `city`).
- **Redundant:** the person already exists in the database (same email, or same phone with a very similar name).
- **False positive:** the entry looks like a valid record but fails verification (bad email format, invalid phone, junk or test name, disposable email domain). It is rejected and logged.
- **Unique:** a new, verified person. Only this class is appended to the `records` table.
- **Cloud database:** MySQL on AWS RDS, app on AWS EC2.

## 3. Requirements and where they are met

| ID | Requirement | Implementation |
|----|-------------|----------------|
| R1 | Classify as UNIQUE / REDUNDANT / FALSE_POSITIVE | `app/classifier.py`, `app/validators.py` |
| R2 | Validate new data against existing data | `app/services.py` (DB lookup before insert) |
| R3 | Prevent duplicates from entering the database | App check + `UNIQUE` keys in `sql/schema.sql` |
| R4 | Append only unique, verified entries | Insert happens only for verdict `UNIQUE` |
| R5 | Accuracy and efficiency | Normalization, indexed UNIQUE keys, `audit_log` table |

## 4. Classification rules
1. Validation fails -> `FALSE_POSITIVE` (stored only in `audit_log`).
2. Email (normalized) already exists -> `REDUNDANT`.
3. Phone (normalized) exists and name similarity >= 0.85 -> `REDUNDANT`.
4. Database UNIQUE constraint rejects the insert (race condition) -> `REDUNDANT`.
5. Otherwise -> `UNIQUE`, inserted into `records`.

## 5. Acceptance criteria
- A valid new person is saved and the verdict is `UNIQUE`.
- Same email with different letter case is `REDUNDANT`.
- `a.li+news@gmail.com` and `ali@gmail.com` are `REDUNDANT`.
- `0300-1234567` and `+92 300 1234567` are the same phone number.
- Invalid email, junk name (e.g. "test", "asdf") or invalid phone is `FALSE_POSITIVE`.
- Two simultaneous identical requests store only one record.
- Every submission, accepted or rejected, appears in `audit_log`.
- All SQL uses prepared statements; no secrets are committed to Git.

## 6. Out of scope
Bulk CSV import, fuzzy matching beyond name similarity, user login, auto scaling (covered in other tasks).