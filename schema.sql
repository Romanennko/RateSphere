CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_username ON users (username);

CREATE TYPE item_status_enum AS ENUM (
    'Completed',
    'In Progress',
    'Planned',
    'Dropped',
    'Ongoing'
);

CREATE TABLE rated_items (
    item_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,

    name VARCHAR(255) NOT NULL,
    alt_name VARCHAR(255),
    item_type VARCHAR(100) NOT NULL,
    status item_status_enum NOT NULL ,
    rating SMALLINT CHECK (rating >= 1 AND rating <= 10) NOT NULL,
    review TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_rated_items_user_id ON rated_items (user_id);
CREATE INDEX idx_rated_items_item_type ON rated_items (item_type);
CREATE INDEX idx_rated_items_status ON rated_items (status);
CREATE INDEX idx_rated_items_rating ON rated_items (rating);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_item_updated_at
BEFORE UPDATE ON rated_items
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();