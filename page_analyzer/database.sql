CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,  -- Добавлено UNIQUE
    created_at TIMESTAMP DEFAULT NOW()
);