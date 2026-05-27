/* # Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only */
CREATE TABLE IF NOT EXISTS kv_storage (
    key TEXT PRIMARY KEY,
    value BLOB,
    expires_at REAL
);

CREATE INDEX IF NOT EXISTS idx_kv_storage_expires_at ON kv_storage(expires_at);
