DROP DATABASE IF EXISTS `telegram_message`;
CREATE DATABASE IF NOT EXISTS `telegram_message`;

USE `telegram_message`;

DROP TABLE IF EXISTS `en`;
CREATE TABLE IF NOT EXISTS `en` (
    `id` INT AUTO_INCREMENT,
    `message` TEXT NOT NULL,
    `insert_time` DATETIME,
    PRIMARY KEY (id)
);

DROP TABLE IF EXISTS `ar`;
CREATE TABLE IF NOT EXISTS `ar` (
    `id` INT AUTO_INCREMENT,
    `message` TEXT NOT NULL,
    `insert_time` DATETIME,
    PRIMARY KEY (id)
);
