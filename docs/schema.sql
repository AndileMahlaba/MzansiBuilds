-- MzansiBuilds logical schema (PostgreSQL / Supabase).
-- Production uses Supabase Postgres; local dev may use SQLite with the same ORM models.
-- This file documents the structure for reviewers (see docs/README.md).

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    bio VARCHAR(500) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_users_email ON users (email);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    stage VARCHAR(40) NOT NULL,
    support_needed VARCHAR(200) DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_projects_user_id ON projects (user_id);
CREATE INDEX ix_projects_stage ON projects (stage);
CREATE INDEX ix_projects_status ON projects (status);
CREATE INDEX ix_projects_created_at ON projects (created_at);

CREATE TABLE milestones (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    achieved_at DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_milestones_project_id ON milestones (project_id);
CREATE INDEX ix_milestones_achieved_at ON milestones (achieved_at);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_comments_project_id ON comments (project_id);
CREATE INDEX ix_comments_created_at ON comments (created_at);

CREATE TABLE collaboration_requests (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    requester_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    message VARCHAR(500) DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_collab_project_id ON collaboration_requests (project_id);
