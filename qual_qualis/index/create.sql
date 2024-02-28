DROP TABLE IF EXISTS term_frequency;
DROP TABLE IF EXISTS inv_doc_frequency;
DROP TABLE IF EXISTS venue;

CREATE TABLE venue (
    `type` INT NOT NULL,
    `hash` BLOB NOT NULL,
    `name` TEXT NOT NULL,
    `qualis` TEXT NOT NULL,
    `extra` TEXT,
    PRIMARY KEY (`type`, `hash`)
);

CREATE TABLE inv_doc_frequency (
    `token` TEXT NOT NULL,
    `idf` REAL NOT NULL,
    PRIMARY KEY (`token`)
);

CREATE TABLE term_frequency (
    `token` TEXT NOT NULL,
    `venue_hash` INT NOT NULL,
    `venue_type` INT NOT NULL,
    `tf` REAL NOT NULL,
    PRIMARY KEY (`token`, `venue_hash`, `venue_type`),
    FOREIGN KEY (`token`) REFERENCES inv_doc_frequency (`token`),
    FOREIGN KEY (`venue_hash`, `venue_type`) REFERENCES venue (`hash`, `type`)
);
