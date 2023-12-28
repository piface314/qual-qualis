DROP TABLE IF EXISTS term_frequency;
DROP TABLE IF EXISTS inv_doc_frequency;
DROP TABLE IF EXISTS venue;

CREATE TABLE venue (
    `type` INT NOT NULL,
    `slug` TEXT NOT NULL,
    `name` TEXT NOT NULL,
    `qualis` TEXT NOT NULL,
    `extra` TEXT,
    PRIMARY KEY (`type`, `slug`)
);

CREATE TABLE inv_doc_frequency (
    `token` TEXT NOT NULL,
    `idf` REAL NOT NULL,
    PRIMARY KEY (`token`)
);

CREATE TABLE term_frequency (
    `token` TEXT NOT NULL,
    `venue_slug` INT NOT NULL,
    `venue_type` INT NOT NULL,
    `tf` REAL NOT NULL,
    PRIMARY KEY (`token`, `venue_slug`, `venue_type`),
    FOREIGN KEY (`token`) REFERENCES inv_doc_frequency (`token`),
    FOREIGN KEY (`venue_slug`, `venue_type`) REFERENCES venue (`slug`, `type`)
);
