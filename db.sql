-- SQL dump generated using DBML (dbml.dbdiagram.io)
-- Database: MySQL

DROP DATABASE `issa`;

CREATE DATABASE `issa`;

USE `issa`;

CREATE TABLE `users` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `username` varchar(64),
  `created_at` timestamp
);

CREATE TABLE `ratings` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `rating` float(8),
  `user_id` bigint(8),
  `isbn` bigint(13),
  `author_id` bigint(8),
  `body` text,
  `rated_at` timestamp
);

CREATE TABLE `books` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `owner_id` bigint(8),
  `title` varchar(64),
  `isbn` bigint(8),
  `rating` float(8),
  `author_id` bigint(8),
  `location_id` bigint(8),
  `status` varchar(16),
  `created_at` timestamp,
  `last_used` timestamp,
  `embedding` bigint(8)
);

CREATE TABLE `isbn` (
  `id` bigint(8) AUTO_INCREMENT PRIMARY KEY,
  `isbn` bigint(13)
);

CREATE TABLE `ratingstoisbn` (
   `id` bigint(8) AUTO_INCREMENT PRIMARY KEY,
   `rating` bigint(8),
   `isbn` bigint(8)
);

CREATE TABLE `checkouts` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `book` bigint(8),
  `checkout_at` timestamp
);

CREATE TABLE `embedding` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `genre` bigint(8),
  `params` bigint(8),
  `published_in` date
);

CREATE TABLE `authors` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `full_name` varchar(64),
  `rating` float(8)
);

CREATE TABLE `location` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `common_name` varchar(64),
  `building_id` bigint(8),
  `shelf` bigint(8),
  `storey` bigint(8)
);

CREATE TABLE `buildings` (
  `id` bigint AUTO_INCREMENT PRIMARY KEY,
  `common_name` varchar(64)
);

ALTER TABLE `books` ADD FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`);

ALTER TABLE `ratings` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `ratingstoisbn` ADD FOREIGN KEY (`isbn`) REFERENCES `isbn` (`id`);

ALTER TABLE `ratingstoisbn` ADD FOREIGN KEY (`rating`) REFERENCES `ratings` (`id`);

ALTER TABLE `books` ADD FOREIGN KEY (`author_id`) REFERENCES `authors` (`id`);

ALTER TABLE `location` ADD FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`);

ALTER TABLE `books` ADD FOREIGN KEY (`location_id`) REFERENCES `location` (`id`);

ALTER TABLE `embedding` ADD FOREIGN KEY (`id`) REFERENCES `users` (`id`);

ALTER TABLE `embedding` ADD FOREIGN KEY (`id`) REFERENCES `isbn` (`isbn`);

ALTER TABLE `books` ADD FOREIGN KEY (`isbn`) REFERENCES `isbn` (`id`);

ALTER TABLE `checkouts` ADD FOREIGN KEY (`book`) REFERENCES `books` (`id`);
