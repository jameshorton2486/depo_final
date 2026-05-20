CREATE TABLE IF NOT EXISTS law_firms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reporting_firms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    main_phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reporting_firm_offices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporting_firm_id INTEGER NOT NULL,
    office_name TEXT NOT NULL,
    address_line_1 TEXT,
    address_line_2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    phone TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporting_firm_id) REFERENCES reporting_firms(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_name TEXT NOT NULL,
    caption TEXT,
    cause_number TEXT,
    venue TEXT,
    jurisdiction TEXT,
    case_status TEXT NOT NULL DEFAULT 'intake',
    reporting_firm_id INTEGER,
    reporting_firm_office_id INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporting_firm_id) REFERENCES reporting_firms(id),
    FOREIGN KEY (reporting_firm_office_id) REFERENCES reporting_firm_offices(id)
);

CREATE TABLE IF NOT EXISTS parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    party_name TEXT NOT NULL,
    party_type TEXT,
    side TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attorneys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    law_firm_id INTEGER,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    bar_number TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (law_firm_id) REFERENCES law_firms(id)
);

CREATE TABLE IF NOT EXISTS case_attorneys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    attorney_id INTEGER NOT NULL,
    party_id INTEGER,
    role TEXT,
    speaker_label TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY (attorney_id) REFERENCES attorneys(id) ON DELETE CASCADE,
    FOREIGN KEY (party_id) REFERENCES parties(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    session_name TEXT NOT NULL,
    session_date TEXT,
    start_time TEXT,
    end_time TEXT,
    location TEXT,
    deponent_name TEXT,
    officer_name TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transcript_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    source_format TEXT,
    deepgram_json_path TEXT,
    keyterms_path TEXT,
    preprocessing_metadata_path TEXT,
    snr_value REAL,
    utt_split_value REAL,
    is_primary INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exhibits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    exhibit_label TEXT NOT NULL,
    exhibit_path TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interpreters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    interpreter_name TEXT NOT NULL,
    language TEXT,
    certification_details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS session_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_time REAL,
    details_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS speaker_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    transcript_asset_id INTEGER,
    speaker_index INTEGER NOT NULL,
    speaker_label TEXT,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (transcript_asset_id) REFERENCES transcript_assets(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS transcript_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    speaker_segment_id INTEGER,
    block_index INTEGER NOT NULL,
    block_type TEXT NOT NULL CHECK (
        block_type IN (
            'COLLOQUY',
            'EXAMINATION_Q',
            'EXAMINATION_A',
            'REPORTER_STATEMENT',
            'INTERPRETER_STATEMENT',
            'PARENTHETICAL',
            'OBJECTION',
            'PROCEEDINGS'
        )
    ),
    speaker_index INTEGER,
    raw_text TEXT NOT NULL,
    working_text TEXT,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    is_edited INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (speaker_segment_id) REFERENCES speaker_segments(id) ON DELETE SET NULL,
    UNIQUE (session_id, block_index)
);

CREATE TABLE IF NOT EXISTS word_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_block_id INTEGER NOT NULL,
    word_index INTEGER NOT NULL,
    word_text TEXT NOT NULL,
    modified_text TEXT,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    is_filler INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transcript_block_id) REFERENCES transcript_blocks(id) ON DELETE CASCADE,
    UNIQUE (transcript_block_id, word_index)
);
