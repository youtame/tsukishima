-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create User table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_code VARCHAR(50) NOT NULL UNIQUE, -- Ex: '224999'
    name VARCHAR(100) NOT NULL,            -- Ex: 'Genius Railway'
    face_embedding vector(512), -- For ArcFace 512-dimensional vectors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);