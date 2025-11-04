-- =====================================================
-- SCHEMA: Интерактивный дашборд оценки эффективности глав МО Липецкой области
-- =====================================================

-- Справочник муниципальных образований
CREATE TABLE dim_mo (
    mo_id SERIAL PRIMARY KEY,
    mo_name VARCHAR(255) NOT NULL UNIQUE,
    oktmo VARCHAR(11),
    okato VARCHAR(5),
    lat DECIMAL(10, 8),
    lon DECIMAL(11, 8),
    geojson_id VARCHAR(50),
    population INTEGER,
    area_km2 DECIMAL(10, 2),
    type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Справочник периодов
CREATE TABLE dim_period (
    period_id SERIAL PRIMARY KEY,
    period_type VARCHAR(20) NOT NULL, -- 'month', 'halfyear', 'year'
    date_from DATE NOT NULL,
    date_to DATE NOT NULL,
    edg_flag BOOLEAN DEFAULT FALSE, -- признак периода ЕДГ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Справочник индикаторов (показателей)
CREATE TABLE dim_indicator (
    ind_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    block VARCHAR(100), -- блок методики
    description TEXT,
    unit VARCHAR(50),
    is_public BOOLEAN DEFAULT TRUE,
    owner_org VARCHAR(100), -- ведомство-владелец
    weight DECIMAL(5, 2), -- вес показателя
    min_value DECIMAL(10, 2),
    max_value DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Справочник штрафов
CREATE TABLE dim_penalty (
    pen_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_org VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Справочник версий методики
CREATE TABLE dim_methodology (
    version_id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    valid_from DATE NOT NULL,
    valid_to DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Справочник шкал оценки (по версиям методики)
CREATE TABLE map_scale (
    scale_id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL REFERENCES dim_methodology(version_id),
    ind_id INTEGER REFERENCES dim_indicator(ind_id),
    pen_id INTEGER REFERENCES dim_penalty(pen_id),
    zone VARCHAR(20), -- 'green', 'yellow', 'red'
    min_score DECIMAL(10, 2),
    max_score DECIMAL(10, 2),
    color_hex VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_one_entity CHECK (
        (ind_id IS NOT NULL AND pen_id IS NULL) OR
        (ind_id IS NULL AND pen_id IS NOT NULL)
    )
);

-- Справочник источников данных
CREATE TABLE src_registry (
    source_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    org VARCHAR(100) NOT NULL,
    contact VARCHAR(255),
    channel VARCHAR(50), -- 'API', 'SFTP', 'Excel', 'Manual'
    schedule VARCHAR(100), -- периодичность
    format VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ФАКТИЧЕСКИЕ ТАБЛИЦЫ
-- =====================================================

-- Факты по индикаторам
CREATE TABLE fact_indicator (
    fact_ind_id SERIAL PRIMARY KEY,
    mo_id INTEGER NOT NULL REFERENCES dim_mo(mo_id),
    period_id INTEGER NOT NULL REFERENCES dim_period(period_id),
    ind_id INTEGER NOT NULL REFERENCES dim_indicator(ind_id),
    version_id INTEGER NOT NULL REFERENCES dim_methodology(version_id),
    value_raw DECIMAL(15, 4), -- исходное значение
    value_norm DECIMAL(10, 4), -- нормализованное значение (0-100)
    score DECIMAL(5, 2), -- баллы
    target DECIMAL(15, 4), -- целевое значение
    source_id INTEGER REFERENCES src_registry(source_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (mo_id, period_id, ind_id, version_id)
);

-- Факты по штрафам
CREATE TABLE fact_penalty (
    fact_pen_id SERIAL PRIMARY KEY,
    mo_id INTEGER NOT NULL REFERENCES dim_mo(mo_id),
    period_id INTEGER NOT NULL REFERENCES dim_period(period_id),
    pen_id INTEGER NOT NULL REFERENCES dim_penalty(pen_id),
    version_id INTEGER NOT NULL REFERENCES dim_methodology(version_id),
    score_negative DECIMAL(5, 2), -- отрицательный балл
    details TEXT,
    source_id INTEGER REFERENCES src_registry(source_id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- События (встречи, конфликты, награды и т.д.)
CREATE TABLE fact_events (
    event_id SERIAL PRIMARY KEY,
    mo_id INTEGER NOT NULL REFERENCES dim_mo(mo_id),
    event_date DATE NOT NULL,
    event_type VARCHAR(50), -- 'meeting', 'conflict', 'award', etc.
    title VARCHAR(255),
    description TEXT,
    link VARCHAR(500),
    source_id INTEGER REFERENCES src_registry(source_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Сводные баллы по МО
CREATE TABLE fact_summary (
    summary_id SERIAL PRIMARY KEY,
    mo_id INTEGER NOT NULL REFERENCES dim_mo(mo_id),
    period_id INTEGER NOT NULL REFERENCES dim_period(period_id),
    version_id INTEGER NOT NULL REFERENCES dim_methodology(version_id),
    score_public DECIMAL(6, 2), -- баллы публичного рейтинга
    score_closed DECIMAL(6, 2), -- баллы закрытого рейтинга
    score_penalties DECIMAL(6, 2), -- штрафные баллы
    score_total DECIMAL(6, 2), -- итоговый балл
    zone VARCHAR(20), -- 'green', 'yellow', 'red'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (mo_id, period_id, version_id)
);

-- =====================================================
-- ЖУРНАЛИРОВАНИЕ
-- =====================================================

-- Журнал аудита
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    actor_id INTEGER,
    action VARCHAR(50),
    entity VARCHAR(100),
    entity_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Журнал загрузок
CREATE TABLE upload_log (
    upload_id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES src_registry(source_id),
    file_name VARCHAR(255),
    file_hash VARCHAR(64),
    records_count INTEGER,
    status VARCHAR(50), -- 'pending', 'processing', 'success', 'error'
    error_message TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Флаги качества данных
CREATE TABLE data_quality_flags (
    flag_id SERIAL PRIMARY KEY,
    mo_id INTEGER REFERENCES dim_mo(mo_id),
    period_id INTEGER REFERENCES dim_period(period_id),
    ind_id INTEGER REFERENCES dim_indicator(ind_id),
    flag_type VARCHAR(50), -- 'anomaly', 'missing', 'inconsistent', etc.
    severity VARCHAR(20), -- 'info', 'warning', 'error'
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ИНДЕКСЫ
-- =====================================================

CREATE INDEX idx_fact_indicator_mo_period ON fact_indicator(mo_id, period_id);
CREATE INDEX idx_fact_indicator_mo_ind ON fact_indicator(mo_id, ind_id);
CREATE INDEX idx_fact_penalty_mo_period ON fact_penalty(mo_id, period_id);
CREATE INDEX idx_fact_summary_mo_period ON fact_summary(mo_id, period_id);
CREATE INDEX idx_fact_events_mo_date ON fact_events(mo_id, event_date);
CREATE INDEX idx_audit_log_ts ON audit_log(ts);
CREATE INDEX idx_upload_log_status ON upload_log(status);
