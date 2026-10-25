
CREATE DATABASE IF NOT EXISTS redundancy_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE redundancy_db;


CREATE TABLE IF NOT EXISTS records (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  full_name   VARCHAR(100) NOT NULL,
  email       VARCHAR(254) NOT NULL,          -- as the user typed it
  email_norm  VARCHAR(254) NOT NULL,          -- cleaned (lowercase, gmail dots removed)
  phone       VARCHAR(30)  NOT NULL,          -- as the user typed it
  phone_norm  VARCHAR(20)  NOT NULL,          -- digits only, country code 92
  city        VARCHAR(80)  NULL,
  fingerprint CHAR(64)     NOT NULL,          -- SHA-256 of the cleaned record
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_email_norm  (email_norm),     -- DB-level duplicate guard 1
  UNIQUE KEY uq_fingerprint (fingerprint),    -- DB-level duplicate guard 2
  KEY idx_phone_norm (phone_norm)             -- speeds up phone lookups
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS audit_log (
  id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  submitted_name    VARCHAR(255) NULL,
  submitted_email   VARCHAR(255) NULL,
  submitted_phone   VARCHAR(255) NULL,
  submitted_city    VARCHAR(255) NULL,
  verdict           ENUM('UNIQUE','REDUNDANT','FALSE_POSITIVE') NOT NULL,
  reason            VARCHAR(255) NOT NULL,
  matched_record_id INT UNSIGNED NULL,        -- which existing record it duplicated
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_verdict (verdict)
) ENGINE=InnoDB;