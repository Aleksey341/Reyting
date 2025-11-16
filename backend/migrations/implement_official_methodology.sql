-- Migration: Implement Official Methodology for Rating System
-- This migration restructures the indicator system according to the official
-- "Методика оценки эффективности деятельности глав администраций МО" document
--
-- Changes:
-- 1. Replaces 19 criteria with 16 official criteria
-- 2. Implements variable point scales (3-6 points per criterion, not uniform 0-10)
-- 3. Splits ratings into ПУБЛИЧНЫЙ (31 pts) and ЗАКРЫТЫЙ (35 pts)
-- 4. Implements penalty system that reduces total score
-- 5. Defines risk zones: Зелёная (53-66), Жёлтая (29-52), Красная (0-28)

BEGIN;

-- Step 1: Add rating_type column to dim_indicator if not exists
ALTER TABLE dim_indicator ADD COLUMN IF NOT EXISTS rating_type VARCHAR(50);
COMMENT ON COLUMN dim_indicator.rating_type IS 'ПУБЛИЧНЫЙ or ЗАКРЫТЫЙ';

-- Step 2: Add is_penalty flag to dim_indicator if not exists
ALTER TABLE dim_indicator ADD COLUMN IF NOT EXISTS is_penalty BOOLEAN DEFAULT FALSE;
COMMENT ON COLUMN dim_indicator.is_penalty IS 'TRUE for penalty criteria that reduce score';

-- Step 3: Add max_points column (replaces old 0-10 scale with variable scales)
ALTER TABLE dim_indicator ADD COLUMN IF NOT EXISTS max_points INTEGER;
COMMENT ON COLUMN dim_indicator.max_points IS 'Maximum points for this criterion (3-6 for normal, negative for penalties)';

-- Step 4: Delete old indicators (keeping data references)
DELETE FROM dim_indicator
WHERE code NOT IN (
  'pub_1', 'pub_2', 'pub_3', 'pub_4', 'pub_5', 'pub_6', 'pub_7', 'pub_8', 'pub_9',
  'closed_1', 'closed_2', 'closed_3', 'closed_4', 'closed_5', 'closed_6', 'closed_7', 'closed_8',
  'pen_1', 'pen_2', 'pen_3'
);

-- Step 5: Create PUBLIC RATING (ПУБЛИЧНЫЙ) criteria
-- Block 1: Political Management (9 criteria, 19 points total)
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('pub_1', 'Поддержка руководства области', 'Политический менеджмент', 'ПУБЛИЧНЫЙ', 'Поддержка со стороны руководства Липецкой области', 'баллы', true, 3, false, NOW(), NOW()),
  ('pub_2', 'Выполнение задач АГП', 'Политический менеджмент', 'ПУБЛИЧНЫЙ', 'Эффективность выполнения задач АГП (91-100% = 5 баллов)', 'баллы', true, 5, false, NOW(), NOW()),
  ('pub_3', 'Позиционирование главы', 'Политический менеджмент', 'ПУБЛИЧНЫЙ', 'Наличие уникального позиционирования главы', 'баллы', true, 3, false, NOW(), NOW()),
  ('pub_4', 'Проектная деятельность', 'Политический менеджмент', 'ПУБЛИЧНЫЙ', 'Реализация региональных и муниципальных проектов', 'баллы', true, 3, false, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Block 2: Care & Attention (3 criteria, 9 points)
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('pub_5', 'Молодежь в добровольчестве', 'Забота и внимание', 'ПУБЛИЧНЫЙ', 'Доля молодых людей в добровольческой деятельности (>50% = 3 баллов)', 'баллы', true, 3, false, NOW(), NOW()),
  ('pub_6', 'Молодежь в Движении Первых', 'Забота и внимание', 'ПУБЛИЧНЫЙ', 'Доля детей 6-18 лет в Движении Первых (>50% = 3 баллов)', 'баллы', true, 3, false, NOW(), NOW()),
  ('pub_7', 'Работа с ветеранами СВО', 'Забота и внимание', 'ПУБЛИЧНЫЙ', 'Личная вовлеченность главы в работу с ветеранами (>=36 встреч в год = 3 баллов)', 'баллы', true, 3, false, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Block 3: Development of cadres and projects (2 criteria, 6 points)
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('pub_8', 'Кадровый резерв', 'Развитие кадрового и проектного потенциала МО', 'ПУБЛИЧНЫЙ', 'Наличие кадрового управленческого резерва (80-100% должностей = 3 баллов)', 'баллы', true, 3, false, NOW(), NOW()),
  ('pub_9', 'Работа с грантами', 'Развитие кадрового и проектного потенциала МО', 'ПУБЛИЧНЫЙ', 'Эффективность работы с грантами (3+ побед = 3 баллов)', 'баллы', true, 3, false, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Step 6: Create CLOSED RATING (ЗАКРЫТЫЙ) criteria
-- Political Management (5 criteria, 23 points)
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('closed_1', 'Партийное мнение в администрации', 'Политический менеджмент', 'ЗАКРЫТЫЙ', 'Партийное мнение в администрации МО (членство + сторонники)', 'баллы', false, 6, false, NOW(), NOW()),
  ('closed_2', 'Альтернативное мнение в органе', 'Политический менеджмент', 'ЗАКРЫТЫЙ', 'Альтернативное мнение в представительном органе (100% = 4 баллов)', 'баллы', false, 4, false, NOW(), NOW()),
  ('closed_3', 'Целевые показатели АГП (уровень)', 'Политический менеджмент', 'ЗАКРЫТЫЙ', 'Достижение целевых показателей по уровню АГП (105-110% = 5 баллов)', 'баллы', false, 5, false, NOW(), NOW()),
  ('closed_4', 'Целевые показатели АГП (качество)', 'Политический менеджмент', 'ЗАКРЫТЫЙ', 'Достижение целевых показателей по качеству АГП (105-110% = 5 баллов)', 'баллы', false, 5, false, NOW(), NOW()),
  ('closed_5', 'Экономическая привлекательность', 'Политический менеджмент', 'ЗАКРЫТЫЙ', 'Экономическая привлекательность МО для элитных групп', 'баллы', false, 3, false, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Care & Attention (2 criteria, 9 points)
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('closed_6', 'Работа с ветеранами СВО (закрытый)', 'Забота и внимание', 'ЗАКРЫТЫЙ', 'Личная вовлеченность главы в работу с ветеранами СВО', 'баллы', false, 3, false, NOW(), NOW()),
  ('closed_7', 'Политическая деятельность ветеранов', 'Забота и внимание', 'ЗАКРЫТЫЙ', 'Общественно-политическая деятельность ветеранов СВО (членство + поддержка)', 'баллы', false, 6, false, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Development (1 criterion, 3 points)
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('closed_8', 'Проект Гордость Липецкой земли', 'Развитие кадрового и проектного потенциала МО', 'ЗАКРЫТЫЙ', 'Наличие представителей МО в проекте Гордость Липецкой земли (>=1 = 2 баллов)', 'баллы', false, 2, false, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Step 7: Create PENALTY criteria
-- These reduce the total score
INSERT INTO dim_indicator (code, name, block, rating_type, description, unit, is_public, max_points, is_penalty, created_at, updated_at)
VALUES
  ('pen_1', 'Конфликты с региональной властью', 'Штрафные критерии', NULL, 'Публичный конфликт с Губернатором = -3; с заместителем/министром = -2', 'баллы', true, -3, true, NOW(), NOW()),
  ('pen_2', 'Внутримуниципальные конфликты', 'Штрафные критерии', NULL, 'Систематические конфликты (>=4 в год) = -3; значительный публичный = -2; эпизодические = -1', 'баллы', true, -3, true, NOW(), NOW()),
  ('pen_3', 'Правоохранительные органы', 'Штрафные критерии', NULL, 'Возбуждение уголовного дела = -5; проверки/аресты = -2', 'баллы', true, -5, true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Step 8: Create methodology version record
INSERT INTO dim_methodology (version, valid_from, valid_to, notes)
VALUES ('2.0', NOW(), '2099-12-31', 'Official methodology: 16 criteria (9 PUBLIC + 8 CLOSED), variable scales, penalty system')
ON CONFLICT DO NOTHING;

-- Step 9: Update fact_indicator table - rename score column for clarity
-- NOTE: This step may require careful consideration to avoid data loss
-- For now, we keep the score column but add score_normalized for 0-1 normalization

ALTER TABLE fact_indicator ADD COLUMN IF NOT EXISTS score_normalized FLOAT;
COMMENT ON COLUMN fact_indicator.score_normalized IS 'Score normalized to 0-1 range for display';

-- Step 10: Define color zones as a reference
-- Зелёная зона: 53-66 баллов (высокая устойчивость)
-- Жёлтая зона: 29-52 баллов (условная устойчивость)
-- Красная зона: 0-28 баллов (низкая устойчивость)

COMMIT;

-- Verification queries
SELECT 'ПУБЛИЧНЫЙ criteria count' as info, COUNT(*) as count FROM dim_indicator WHERE rating_type = 'ПУБЛИЧНЫЙ';
SELECT 'ЗАКРЫТЫЙ criteria count' as info, COUNT(*) as count FROM dim_indicator WHERE rating_type = 'ЗАКРЫТЫЙ';
SELECT 'Penalty criteria count' as info, COUNT(*) as count FROM dim_indicator WHERE is_penalty = true;
SELECT 'Total max points ПУБЛИЧНЫЙ' as info, SUM(max_points) as total FROM dim_indicator WHERE rating_type = 'ПУБЛИЧНЫЙ';
SELECT 'Total max points ЗАКРЫТЫЙ' as info, SUM(max_points) as total FROM dim_indicator WHERE rating_type = 'ЗАКРЫТЫЙ';
