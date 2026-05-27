/* # Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only */
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (
        lower(hex(randomblob(4))) || '-' ||
        lower(hex(randomblob(2))) || '-' ||
        lower(hex(randomblob(2))) || '-' ||
        lower(hex(randomblob(2))) || '-' ||
        lower(hex(randomblob(6)))
    ),
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO users (id, login, password_hash)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'system',
    '__disabled__'
);

ALTER TABLE reports
ADD COLUMN user_id TEXT REFERENCES users(id);

UPDATE reports
SET user_id = '00000000-0000-0000-0000-000000000001'
WHERE user_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
