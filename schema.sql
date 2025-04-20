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

CREATE TYPE item_content_type_enum AS ENUM (
    'Movie',
    'Book',
    'Manga',
    'Game',
    'Anime',
    'Manhwa',
    'Manhua',
    'Cartoon',
    'Series',
    'Board game'
);

CREATE TABLE rated_items (
    item_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,

    name VARCHAR(255) NOT NULL,
    alt_name VARCHAR(255),
    item_type item_content_type_enum NOT NULL,
    status item_status_enum NOT NULL ,
    rating NUMERIC(4, 2) CHECK (rating >= 1 AND rating <= 10) NULL,
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

CREATE TRIGGER update_user_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE criteria (
    criterion_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NULL,
    default_for_types item_content_type_enum[] NULL,
    is_overall BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_criteria_name ON criteria (name);
CREATE INDEX idx_criteria_is_overall ON criteria (is_overall);


CREATE TABLE item_criterion_ratings (
    rating_id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL,
    criterion_id INTEGER NOT NULL,
    rating NUMERIC(4, 2) NOT NULL CHECK (rating >= 1.0 AND rating <= 10.0),

    CONSTRAINT fk_item
        FOREIGN KEY(item_id)
        REFERENCES rated_items(item_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_criterion
        FOREIGN KEY(criterion_id)
        REFERENCES criteria(criterion_id)
        ON DELETE RESTRICT,

    UNIQUE (item_id, criterion_id)
);

CREATE INDEX idx_item_criterion_ratings_item_id ON item_criterion_ratings (item_id);
CREATE INDEX idx_item_criterion_ratings_criterion_id ON item_criterion_ratings (criterion_id);

INSERT INTO criteria (name, is_overall) VALUES ('Total score', TRUE);

INSERT INTO criteria (name, description, default_for_types) VALUES ('Gameplay', 'Interesting, engaging, variety of mechanics.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Graphics', 'Quality of visual design, style.', ARRAY['Movie', 'Game', 'Anime', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Characters', 'Elaboration, development, charisma.', ARRAY['Movie', 'Book', 'Manga', 'Manhwa', 'Manhua']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Optimization', 'Performance, stability, bug free.', ARRAY['Game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Music and sound', 'Soundtrack, voice-over, soundtrack.', ARRAY['Movie', 'Game', 'Anime', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Replayability', 'Repeatability, variability.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Revisability', 'Look again.', ARRAY['Movie', 'Anime', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Re-readability', 'The possibility of rereading.', ARRAY['Book', 'Manga', 'Manhwa', 'Manhua']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Difficulty level', 'Balance between challenge and comfort.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Social aspects', 'Opportunities for cooperative play or interaction.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Directing', 'Shooting style, frame work, overall vision.', ARRAY['Movie', 'Game', 'Anime', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Acting', 'Emotional authenticity, charisma.', ARRAY['Movie', 'Book', 'Manga', 'Game', 'Anime', 'Manhwa', 'Manhua', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Dialogues', 'Realistic, interesting, deep.', ARRAY['Movie', 'Book', 'Manga', 'Game', 'Anime', 'Manhwa', 'Manhua', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Visual aesthetics', 'Cameraman work, special effects, scenery.', ARRAY['Movie', 'Game', 'Anime', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Themes and ideas', 'Philosophical depth, relevance of the issues.', ARRAY['Movie', 'Book', 'Manga', 'Game', 'Anime', 'Manhwa', 'Manhua', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Final', 'How satisfactory and logical it is.', ARRAY['Movie', 'Book', 'Manga', 'Game', 'Anime', 'Manhwa', 'Manhua', 'Cartoon', 'Series']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Animation', 'Quality, attention to detail, style.', ARRAY['Anime', 'Cartoon']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Rules', 'Simple, intuitive, logical.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Depth of strategy', 'Ability to build tactics and plan.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Components', 'Quality of materials, visual style.', ARRAY['Book', 'Manga', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Balance', 'Equal chances to win, no dominant strategy.', ARRAY['Game', 'Board game']::item_content_type_enum[]);
INSERT INTO criteria (name, description, default_for_types) VALUES ('Accessibility', 'Is it suitable for beginners.', ARRAY['Game', 'Board game']::item_content_type_enum[]);

INSERT INTO criteria (name, description) VALUES ('Plot', 'Interesting, logical, unexpected twists and turns.');
INSERT INTO criteria (name, description) VALUES ('Pace of narration', 'Dynamism, no drawn out moments.');
INSERT INTO criteria (name, description) VALUES ('Originality', 'Uniqueness of concept or pitch.');
INSERT INTO criteria (name, description) VALUES ('Emotional response', 'A ability to evoke emotion.');
INSERT INTO criteria (name, description) VALUES ('Atmosphere', 'How addictive the world is.');
INSERT INTO criteria (name, description) VALUES ('World', 'Elaboration, immersion, uniqueness.');
INSERT INTO criteria (name, description) VALUES ('Duration', 'Optimal batch duration.');

