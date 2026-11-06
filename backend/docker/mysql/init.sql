-- CivicTrack MySQL bootstrap.
-- The database is created by the official image; this file fixes its charset
-- and verifies UTC is the server timezone.
ALTER DATABASE civictrack CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
SET time_zone = '+00:00';
