-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create User table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    face_embedding vector(512), -- For ArcFace 512-dimensional vectors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);