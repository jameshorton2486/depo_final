CREATE TABLE IF NOT EXISTS law_firms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address_line_1 TEXT,
    address_line_2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    phone TEXT,
    email TEXT,
    source_document TEXT,
    extracted_from TEXT,
    parser_confidence REAL,
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
    case_style TEXT,
    cause_number TEXT,
    venue TEXT,
    jurisdiction TEXT,
    district_division TEXT,
    county TEXT,
    court_type TEXT,
    state TEXT,
    case_status TEXT NOT NULL DEFAULT 'intake',
    reporting_firm_id INTEGER,
    reporting_firm_office_id INTEGER,
    source_document TEXT,
    extracted_from TEXT,
    parser_confidence REAL,
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
    role_modifier TEXT,
    alias_name TEXT,
    entity_type TEXT,
    related_party_name TEXT,
    source_document TEXT,
    extracted_from TEXT,
    parser_confidence REAL,
    manual_override INTEGER NOT NULL DEFAULT 0,
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
    bar_state TEXT,
    address_line_1 TEXT,
    address_line_2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    fax TEXT,
    represented_party TEXT,
    source_document TEXT,
    extracted_from TEXT,
    parser_confidence REAL,
    manual_override INTEGER NOT NULL DEFAULT 0,
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
    represented_party_name TEXT,
    is_lead INTEGER NOT NULL DEFAULT 0,
    source_document TEXT,
    extracted_from TEXT,
    parser_confidence REAL,
    manual_override INTEGER NOT NULL DEFAULT 0,
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
    location_type TEXT,
    location_address TEXT,
    deponent_name TEXT,
    officer_name TEXT,
    ordered_by TEXT,
    service_type TEXT,
    csr_required INTEGER NOT NULL DEFAULT 0,
    source_document TEXT,
    extracted_from TEXT,
    parser_confidence REAL,
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

CREATE TABLE IF NOT EXISTS review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    reviewer TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    reviewer_notes TEXT,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    word_object_id INTEGER,
    transcript_block_id INTEGER,
    speaker_segment_id INTEGER,
    issue_category TEXT NOT NULL,
    confidence_level TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    source TEXT NOT NULL DEFAULT 'automatic',
    note TEXT,
    original_value TEXT,
    current_value TEXT,
    reviewer TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (word_object_id) REFERENCES word_objects(id) ON DELETE CASCADE,
    FOREIGN KEY (transcript_block_id) REFERENCES transcript_blocks(id) ON DELETE CASCADE,
    FOREIGN KEY (speaker_segment_id) REFERENCES speaker_segments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS review_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_flag_id INTEGER NOT NULL,
    review_session_id INTEGER,
    action_type TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    note TEXT,
    original_value TEXT,
    modified_value TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_flag_id) REFERENCES review_flags(id) ON DELETE CASCADE,
    FOREIGN KEY (review_session_id) REFERENCES review_sessions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS speaker_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    speaker_segment_id INTEGER NOT NULL,
    original_speaker_label TEXT NOT NULL,
    corrected_speaker_label TEXT NOT NULL,
    corrected_role TEXT,
    reviewer TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (speaker_segment_id) REFERENCES speaker_segments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transcript_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    issue_category TEXT,
    original_value TEXT,
    modified_value TEXT,
    reviewer TEXT NOT NULL,
    correction_source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
