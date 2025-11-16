-- Migration: Create criteria blocks and populate all 19 criteria with proper hierarchy
-- Date: 2025-11-16
-- Purpose: Establish structured hierarchy: Block → Criteria → Indicators

BEGIN;

-- 1. Create dim_criteria_block table for organizing criteria into blocks
CREATE TABLE IF NOT EXISTS dim_criteria_block (
    block_id SERIAL PRIMARY KEY,
    block_name VARCHAR(255) NOT NULL UNIQUE,
    block_order INTEGER,
    description TEXT,
    is_visible BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Add block_id to dim_indicator (if not exists)
ALTER TABLE dim_indicator ADD COLUMN IF NOT EXISTS block_id INTEGER REFERENCES dim_criteria_block(block_id);
ALTER TABLE dim_indicator ADD COLUMN IF NOT EXISTS criteria_order INTEGER;

-- 3. Insert criteria blocks (categories)
INSERT INTO dim_criteria_block (block_name, block_order, description, is_visible) VALUES
    ('Политический менеджмент', 1, 'Критерии политического управления МО', true),
    ('Забота и внимание', 2, 'Критерии социальной политики и вовлеченности', true),
    ('Развитие кадрового и проектного потенциала МО', 3, 'Критерии развития кадров и проектов', true),
    ('Штрафные критерии', 4, 'Критерии с отрицательными баллами', true)
ON CONFLICT DO NOTHING;

-- 4. Insert criteria into dim_indicator with proper block assignment
INSERT INTO dim_indicator (code, name, block, description, unit, is_public, weight, created_at, updated_at) VALUES
    -- Блок 1: Политический менеджмент (9 критериев)
    ('pm_01', 'Оценка поддержки руководства области', 'Политический менеджмент', 'Уровень поддержки главой МО региональной администрации', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_02', 'Выполнение задач АГП', 'Политический менеджмент', 'Выполнение задач Аппарата Губернатора', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_03', 'Позиционирование главы МО', 'Политический менеджмент', 'Статус и видимость главы МО в политическом процессе', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_04', 'Проектная деятельность', 'Политический менеджмент', 'Реализация федеральных и региональных проектов', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_05', 'Партийная принадлежность сотрудников', 'Политический менеджмент', 'Партийная принадлежность сотрудников администрации МО', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_06', 'Распределение мандатов', 'Политический менеджмент', 'Распределение парламентских мандатов', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_07', 'Показатели АГП (Уровень)', 'Политический менеджмент', 'Уровень выполнения показателей АГП', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_08', 'Показатели АГП (Качество)', 'Политический менеджмент', 'Качество выполнения показателей АГП', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('pm_09', 'Экономическая привлекательность МО', 'Политический менеджмент', 'Уровень экономической привлекательности МО', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- Блок 2: Забота и внимание (4 критерия)
    ('ca_01', 'Вовлеченность молодежи (Добровольчество)', 'Забота и внимание', 'Уровень вовлеченности молодежи в добровольческую деятельность', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('ca_02', 'Вовлеченность молодежи (Движение Первых)', 'Забота и внимание', 'Уровень вовлеченности молодежи в Движение Первых', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('ca_03', 'Личная работа главы с ветеранами СВО', 'Забота и внимание', 'Уровень личного взаимодействия главы с ветеранами СВО', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('ca_04', 'Партийная принадлежность ветеранов СВО', 'Забота и внимание', 'Партийная принадлежность ветеранов СВО', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- Блок 3: Развитие кадрового и проектного потенциала (3 критерия)
    ('dev_01', 'Кадровый управленческий резерв', 'Развитие кадрового и проектного потенциала МО', 'Наличие и развитие управленческого кадрового резерва', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('dev_02', 'Работа с грантами', 'Развитие кадрового и проектного потенциала МО', 'Успешность участия в грантовых программах', 'баллы', true, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('dev_03', 'Участие в проекте «Гордость Липецкой земли»', 'Развитие кадрового и проектного потенциала МО', 'Участие и результаты в проекте «Гордость Липецкой земли»', 'баллы', false, 1.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 5. Update penalties table to include block information
ALTER TABLE dim_penalty ADD COLUMN IF NOT EXISTS block VARCHAR(100);

-- Insert penalties with proper structure
INSERT INTO dim_penalty (code, name, description, owner_org, block) VALUES
    ('pen_01', 'Конфликты с региональной властью', 'Наличие конфликтов с органами региональной власти', 'Аппарат Губернатора', 'Штрафные критерии'),
    ('pen_02', 'Внутримуниципальные конфликты', 'Наличие конфликтов внутри муниципального образования', 'Администрация МО', 'Штрафные критерии'),
    ('pen_03', 'Данные правоохранительных органов', 'Информация из правоохранительных органов', 'МВД/СК РФ', 'Штрафные критерии')
ON CONFLICT (code) DO NOTHING;

-- 6. Create a view for easier access to criteria with their blocks
CREATE OR REPLACE VIEW v_criteria_hierarchy AS
SELECT
    b.block_id,
    b.block_name,
    b.block_order,
    i.ind_id,
    i.code,
    i.name as criteria_name,
    i.description,
    i.is_public,
    i.weight
FROM dim_criteria_block b
LEFT JOIN dim_indicator i ON i.block = b.block_name
ORDER BY b.block_order, i.weight DESC;

-- Verification
SELECT * FROM dim_criteria_block ORDER BY block_order;
SELECT COUNT(*) as total_criteria FROM dim_indicator WHERE code LIKE 'pm_%' OR code LIKE 'ca_%' OR code LIKE 'dev_%';
SELECT COUNT(*) as total_penalties FROM dim_penalty WHERE block = 'Штрафные критерии';

COMMIT;
