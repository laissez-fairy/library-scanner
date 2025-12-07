-- SQL dump generated using DBML (dbml.dbdiagram.io)
-- Database: MySQL

CREATE TABLE `users` (
  `id` int PRIMARY KEY,
  `username` varchar(32),
  `created_at` timestamp
);

CREATE TABLE `ratings` (
  `id` int PRIMARY KEY,
  `rating` float(8),
  `user_id` int(8),
  `isbn` int(13),
  `author_id` int(8),
  `body` text,
  `rated_at` timestamp
);

CREATE TABLE `books` (
  `id` int PRIMARY KEY,
  `owner_id` int(8),
  `title` varchar(32),
  `isbn` int(8),
  `rating` float(8),
  `author_id` int(8),
  `location_id` int(8),
  `status` varchar(16),
  `created_at` timestamp,
  `last_used` timestamp,
  `embedding` int(8)
);

CREATE TABLE `isbn` (
  `id` int(8) PRIMARY KEY,
  `isbn` int(13)
);

CREATE TABLE `ratingstoisbn` (
   `id` int(8) PRIMARY KEY,
   `rating` int(8),
   `isbn` int(8)
);

CREATE TABLE `checkouts` (
  `id` int PRIMARY KEY,
  `book` int(8),
  `checkout_at` timestamp
);

CREATE TABLE `embedding` (
  `id` int PRIMARY KEY,
  `genre` int(8),
  `params` int(8),
  `published_in` date
);

CREATE TABLE `authors` (
  `id` int PRIMARY KEY,
  `full_name` varchar(32),
  `rating` float(8)
);

CREATE TABLE `location` (
  `id` int PRIMARY KEY,
  `common_name` varchar(32),
  `building_id` int(8),
  `shelf` int(8),
  `storey` int(8)
);

CREATE TABLE `buildings` (
  `id` int PRIMARY KEY,
  `common_name` varchar(32)
);

ALTER TABLE `books` ADD FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`);

ALTER TABLE `ratings` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

ALTER TABLE `ratingstoisbn` ADD FOREIGN KEY (`isbn`) REFERENCES `isbn` (`id`);

ALTER TABLE `ratingstoisbn` ADD FOREIGN KEY (`rating`) REFERENCES `ratings` (`id`);

ALTER TABLE `books` ADD FOREIGN KEY (`author_id`) REFERENCES `authors` (`id`);

ALTER TABLE `location` ADD FOREIGN KEY (`building_id`) REFERENCES `buildings` (`id`);

ALTER TABLE `books` ADD FOREIGN KEY (`location_id`) REFERENCES `location` (`id`);

ALTER TABLE `users` ADD FOREIGN KEY (`id`) REFERENCES `embedding` (`id`);

ALTER TABLE `isbn` ADD FOREIGN KEY (`isbn`) REFERENCES `embedding` (`id`);

ALTER TABLE `books` ADD FOREIGN KEY (`isbn`) REFERENCES `isbn` (`id`);

ALTER TABLE `checkouts` ADD FOREIGN KEY (`book`) REFERENCES `books` (`id`);
