CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    study_level TEXT,
    study_year INTEGER,
    home_country TEXT,
    ethnicity TEXT,
    gender TEXT,
    major TEXT,
    academic_goal TEXT,  
);