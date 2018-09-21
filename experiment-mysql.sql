-- A simple file to chuck MySQL statements into
-- This just allows quick-and-dirty experiments with the DB for testing

ALTER USER root@172.17.0.1 IDENTIFIED WITH mysql_native_password BY 'my-secret-pw';

SHOW DATABASES;

CREATE DATABASE menagerie;

USE menagerie;

SHOW TABLES;

CREATE TABLE IF NOT EXISTS tasks (
    task_id INT AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    start_date DATE,
    due_date DATE,
    status TINYINT NOT NULL,
    priority TINYINT NOT NULL,
    description TEXT,
    PRIMARY KEY (task_id)
);

DESCRIBE tasks;

DROP DATABASE menagerie;
