/* # Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only */
DROP TABLE IF EXISTS reports;

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY DEFAULT (
        lower(hex(randomblob(4))) || '-' ||
        lower(hex(randomblob(2))) || '-' ||
        lower(hex(randomblob(2))) || '-' ||
        lower(hex(randomblob(2))) || '-' ||
        lower(hex(randomblob(6)))
    ),
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    provenance_data TEXT NULL,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
