from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "download_dir" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "path" VARCHAR(4096) NOT NULL UNIQUE,
    "last_used" TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS "downloader" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "preset" VARCHAR(16) UNIQUE,
    "config" TEXT NOT NULL,
    "name" VARCHAR(64) NOT NULL UNIQUE,
    "host" VARCHAR(255),
    "port" INT,
    "version" VARCHAR(32),
    "priority" INT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "download_task" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "dir" VARCHAR(4096) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "unique_id" VARCHAR(255),
    "info_hash" VARCHAR(40) UNIQUE,
    "info_hash_v2" VARCHAR(68) UNIQUE,
    "magnet_link" TEXT,
    "state" VARCHAR(16) NOT NULL /* DOWNLOADING: downloading
PAUSED: paused
COMPLETED: completed
ERROR: error */,
    "raw_state" VARCHAR(32),
    "error_msg" TEXT,
    "up_speed" BIGINT,
    "dl_speed" BIGINT,
    "percentage" REAL,
    "total_size" BIGINT,
    "completed_size" BIGINT,
    "completed_at" TIMESTAMP,
    "downloader_id" INT NOT NULL REFERENCES "downloader" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_download_ta_unique__669123" ON "download_task" ("unique_id");
CREATE INDEX IF NOT EXISTS "idx_download_ta_downloa_2b9cf3" ON "download_task" ("downloader_id");
CREATE TABLE IF NOT EXISTS "flow_repository" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "repo_name" VARCHAR(255) NOT NULL UNIQUE,
    "repo_url" VARCHAR(255) NOT NULL,
    "repo_description" VARCHAR(512),
    "owner_name" VARCHAR(64),
    "owner_url" VARCHAR(255),
    "owner_avatar" VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS "flow_template" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "path" VARCHAR(255) NOT NULL,
    "name" VARCHAR(64) NOT NULL,
    "icon" VARCHAR(255),
    "description" VARCHAR(255),
    "category" VARCHAR(16) NOT NULL /* INDEXER: indexer
DOWNLOAD: download
INGEST: ingest
MANUAL: manual
SCHEDULE: schedule */,
    "revision" INT NOT NULL,
    "definition" JSON NOT NULL,
    "newest" INT NOT NULL DEFAULT 1,
    "repo_id" VARCHAR(255) NOT NULL REFERENCES "flow_repository" ("repo_name") ON DELETE CASCADE,
    CONSTRAINT "uid_flow_templa_repo_id_08d49a" UNIQUE ("repo_id", "path", "revision")
);
CREATE INDEX IF NOT EXISTS "idx_flow_templa_repo_id_8200b1" ON "flow_template" ("repo_id");
CREATE TABLE IF NOT EXISTS "flow_graph" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(64) NOT NULL UNIQUE,
    "icon" VARCHAR(255),
    "description" VARCHAR(255),
    "category" VARCHAR(16) NOT NULL /* INDEXER: indexer
DOWNLOAD: download
INGEST: ingest
MANUAL: manual
SCHEDULE: schedule */,
    "revision" INT,
    "state" VARCHAR(16) NOT NULL /* DRAFTING: drafting
MODIFIED: modified
PUBLISHED: published */,
    "draft" JSON,
    "definition" JSON,
    "editable" INT NOT NULL DEFAULT 1,
    "tmpl_id" INT REFERENCES "flow_template" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_flow_graph_tmpl_id_1fe60c" ON "flow_graph" ("tmpl_id");
CREATE TABLE IF NOT EXISTS "flow_instance" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "definition" JSON NOT NULL,
    "bootparams" JSON,
    "context" JSON NOT NULL,
    "repeatable" INT NOT NULL DEFAULT 0,
    "asynchronous" INT NOT NULL DEFAULT 0,
    "prev_id" INT,
    "graph_id" INT NOT NULL REFERENCES "flow_graph" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_flow_instan_graph_i_891af6" ON "flow_instance" ("graph_id");
CREATE TABLE IF NOT EXISTS "flow_footprint" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "node_id" VARCHAR(64) NOT NULL,
    "node_type" VARCHAR(64) NOT NULL,
    "node_data" JSON NOT NULL,
    "loop_id" VARCHAR(64),
    "started_at" TIMESTAMP NOT NULL,
    "ended_at" TIMESTAMP NOT NULL,
    "inst_id" INT NOT NULL REFERENCES "flow_instance" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_flow_footpr_inst_id_cdd871" ON "flow_footprint" ("inst_id");
CREATE TABLE IF NOT EXISTS "flow_job" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "bootparams" JSON,
    "repeatable" INT NOT NULL DEFAULT 0,
    "recoverable" INT NOT NULL DEFAULT 1,
    "state" VARCHAR(16) NOT NULL /* PENDING: pending
RUNNING: running
PAUSED: paused */,
    "trigger" VARCHAR(16) NOT NULL /* DATE: date
CRON: cron
INTERVAL: interval */,
    "run_date" TIMESTAMP,
    "cron_expr" VARCHAR(255),
    "interval_num" INT,
    "interval_unit" VARCHAR(16) /* WEEKS: weeks
DAYS: days
HOURS: hours
MINUTES: minutes
SECONDS: seconds */,
    "interval_start" TIMESTAMP,
    "interval_end" TIMESTAMP,
    "graph_id" INT NOT NULL REFERENCES "flow_graph" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_flow_job_graph_i_49701f" ON "flow_job" ("graph_id");
CREATE TABLE IF NOT EXISTS "flow_log" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "bootparams" JSON,
    "retval" JSON,
    "started_at" TIMESTAMP NOT NULL,
    "ended_at" TIMESTAMP,
    "node_id" VARCHAR(64),
    "node_type" VARCHAR(64),
    "node_data" JSON,
    "input_id" VARCHAR(64),
    "exc_info" TEXT,
    "graph_id" INT NOT NULL REFERENCES "flow_graph" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_flow_log_graph_i_dad029" ON "flow_log" ("graph_id");
CREATE TABLE IF NOT EXISTS "flow_trigger" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "category" VARCHAR(16) NOT NULL /* INDEXER: indexer
DOWNLOAD: download
INGEST: ingest
MANUAL: manual
SCHEDULE: schedule */,
    "rel_id" INT NOT NULL,
    "priority" INT NOT NULL,
    "asynchronous" INT NOT NULL DEFAULT 0,
    "graph_id" INT NOT NULL REFERENCES "flow_graph" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_flow_trigge_graph_i_7a1464" UNIQUE ("graph_id", "rel_id"),
    CONSTRAINT "uid_flow_trigge_rel_id_da5280" UNIQUE ("rel_id", "priority")
);
CREATE INDEX IF NOT EXISTS "idx_flow_trigge_graph_i_9c3d56" ON "flow_trigger" ("graph_id");
CREATE TABLE IF NOT EXISTS "flow_variable" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "key" VARCHAR(64) NOT NULL,
    "value" JSON NOT NULL,
    "expires" INT,
    "graph_id" INT NOT NULL REFERENCES "flow_graph" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_flow_variab_graph_i_66dc2e" UNIQUE ("graph_id", "key")
);
CREATE INDEX IF NOT EXISTS "idx_flow_variab_graph_i_367a40" ON "flow_variable" ("graph_id");
CREATE TABLE IF NOT EXISTS "global_cookie" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "name" TEXT NOT NULL,
    "value" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "path" TEXT NOT NULL,
    "expires" INT,
    CONSTRAINT "uid_global_cook_name_a6f15c" UNIQUE ("name", "domain", "path")
);
CREATE TABLE IF NOT EXISTS "global_variable" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "key" VARCHAR(64) NOT NULL UNIQUE,
    "value" VARCHAR(255) NOT NULL,
    "value_length" INT NOT NULL,
    "encrypted" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "media_lib" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "lib_type" VARCHAR(16) NOT NULL /* MOVIE: movie
TV_SHOW: tv_show
MUSIC: music */,
    "name" VARCHAR(64) NOT NULL UNIQUE,
    "dir" VARCHAR(4096) NOT NULL UNIQUE,
    "language" VARCHAR(16) /* EN_US: en-US
ZH_CN: zh-CN */,
    "priority" INT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "media_event" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "src_path" VARCHAR(4096) NOT NULL,
    "dest_path" VARCHAR(4096),
    "event_type" VARCHAR(16) NOT NULL,
    "is_directory" INT NOT NULL DEFAULT 0,
    "lib_id" INT NOT NULL REFERENCES "media_lib" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_media_event_lib_id_3fa0d0" ON "media_event" ("lib_id");
CREATE TABLE IF NOT EXISTS "media_item" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "dir" VARCHAR(4096) NOT NULL,
    "path" VARCHAR(4096) NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "meta" VARCHAR(4096),
    "title" VARCHAR(255),
    "cover" VARCHAR(255),
    "backdrop" VARCHAR(255),
    "year" INT,
    "rating" VARCHAR(40),
    "lib_id" INT NOT NULL REFERENCES "media_lib" ("id") ON DELETE CASCADE,
    "parent_id" INT REFERENCES "media_item" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_media_item_lib_id_2d2952" UNIQUE ("lib_id", "path")
);
CREATE INDEX IF NOT EXISTS "idx_media_item_lib_id_214a6d" ON "media_item" ("lib_id");
CREATE INDEX IF NOT EXISTS "idx_media_item_parent__0bfc6b" ON "media_item" ("parent_id");
CREATE TABLE IF NOT EXISTS "user" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "username" VARCHAR(64) NOT NULL UNIQUE,
    "password" VARCHAR(64) NOT NULL,
    "avatar" VARCHAR(255),
    "role" VARCHAR(16) NOT NULL /* USER: user
ADMIN: admin */,
    "preferences" JSON
);
CREATE TABLE IF NOT EXISTS "user_favorite" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "rsrc_id" VARCHAR(255) NOT NULL,
    "rsrc" JSON NOT NULL,
    "url" VARCHAR(255),
    "indexer_id" INT NOT NULL REFERENCES "flow_graph" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_favori_indexer_ef24be" ON "user_favorite" ("indexer_id");
CREATE INDEX IF NOT EXISTS "idx_user_favori_user_id_6c9674" ON "user_favorite" ("user_id");
CREATE TABLE IF NOT EXISTS "user_history" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_histor_user_id_802ce5" ON "user_history" ("user_id");
CREATE TABLE IF NOT EXISTS "user_session" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "session_id" VARCHAR(32) NOT NULL,
    "user_info" JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
