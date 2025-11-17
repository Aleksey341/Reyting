-- Load Official Methodology Data into fact_indicator table
-- This script imports CSV data with official criteria codes (pub_*, closed_*, pen_*)

-- First, check the latest period
SELECT 'Latest period:' as note, period_id, period_type, date_from
FROM dim_period
ORDER BY period_id DESC
LIMIT 1;

-- Set period ID (change if needed based on the query above)
-- Assuming period_id = 1 for this example
-- You may need to adjust based on your actual period structure

-- Clear existing data for these criteria (optional - comment out if you want to preserve old data)
-- DELETE FROM fact_indicator
-- WHERE ind_id IN (
--   SELECT ind_id FROM dim_indicator
--   WHERE code IN ('pub_1','pub_2','pub_3','pub_4','pub_5','pub_6','pub_7','pub_8','pub_9',
--                  'closed_1','closed_2','closed_3','closed_4','closed_5','closed_6','closed_7','closed_8',
--                  'pen_1','pen_2','pen_3')
-- )
-- AND period_id = 1;

BEGIN TRANSACTION;

-- pub_2: Выполнение задач АГП (scores 0.58-0.95)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, score, NOW(), NOW() FROM (
  VALUES
    ('Липецк', 0.95),
    ('Елец', 0.88),
    ('Воловский', 0.76),
    ('Грязянский', 0.91),
    ('Данковский', 0.65),
    ('Добринский', 0.82),
    ('Добровский', 0.71),
    ('Долгоруковский', 0.93),
    ('Елецкий', 0.58),
    ('Задонский', 0.79),
    ('Измалковский', 0.85),
    ('Краснинский', 0.68),
    ('Лебедянский', 0.77),
    ('Лев-Толстовский', 0.81),
    ('Липецкий', 0.9),
    ('Становлянский', 0.73),
    ('Тербунский', 0.69),
    ('Усманский', 0.84),
    ('Хлевенский', 0.75),
    ('Чаплыгинский', 0.86)
) AS t(mo_name, score)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_2' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_3: Позиционирование главы МО (categorical: 3 = функционер, 0 = размыто)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, CASE positioning
  WHEN 'глава-функционер/хозяйственник' THEN 3
  WHEN 'размытое' THEN 0
  ELSE 1
END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 'глава-функционер/хозяйственник'),
    ('Елец', 'глава-функционер/хозяйственник'),
    ('Воловский', 'размытое'),
    ('Грязянский', 'глава-функционер/хозяйственник'),
    ('Данковский', 'размытое'),
    ('Добринский', 'глава-функционер/хозяйственник'),
    ('Добровский', 'размытое'),
    ('Долгоруковский', 'глава-функционер/хозяйственник'),
    ('Елецкий', 'размытое'),
    ('Задонский', 'глава-функционер/хозяйственник'),
    ('Измалковский', 'глава-функционер/хозяйственник'),
    ('Краснинский', 'размытое'),
    ('Лебедянский', 'глава-функционер/хозяйственник'),
    ('Лев-Толстовский', 'глава-функционер/хозяйственник'),
    ('Липецкий', 'глава-функционер/хозяйственник'),
    ('Становлянский', 'размытое'),
    ('Тербунский', 'размытое'),
    ('Усманский', 'глава-функционер/хозяйственник'),
    ('Хлевенский', 'размытое'),
    ('Чаплыгинский', 'глава-функционер/хозяйственник')
) AS t(mo_name, positioning)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_3' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_4: Проектная деятельность (project count: 0-3)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, score, NOW(), NOW() FROM (
  VALUES
    ('Липецк', 3),
    ('Елец', 2),
    ('Воловский', 1),
    ('Грязянский', 2),
    ('Данковский', 0),
    ('Добринский', 2),
    ('Добровский', 1),
    ('Долгоруковский', 3),
    ('Елецкий', 0),
    ('Задонский', 2),
    ('Измалковский', 2),
    ('Краснинский', 1),
    ('Лебедянский', 1),
    ('Лев-Толстовский', 2),
    ('Липецкий', 3),
    ('Становлянский', 1),
    ('Тербунский', 1),
    ('Усманский', 2),
    ('Хлевенский', 1),
    ('Чаплыгинский', 2)
) AS t(mo_name, score)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_4' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_5: Молодезь в добровольчестве (percentages 0.28-0.52)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, score * 3, NOW(), NOW() FROM (
  VALUES
    ('Липецк', 0.52),
    ('Елец', 0.48),
    ('Воловский', 0.28),
    ('Грязянский', 0.35),
    ('Данковский', 0.32),
    ('Добринский', 0.41),
    ('Добровский', 0.38),
    ('Долгоруковский', 0.50),
    ('Елецкий', 0.29),
    ('Задонский', 0.45),
    ('Измалковский', 0.47),
    ('Краснинский', 0.30),
    ('Лебедянский', 0.42),
    ('Лев-Толстовский', 0.46),
    ('Липецкий', 0.51),
    ('Становлянский', 0.33),
    ('Тербунский', 0.31),
    ('Усманский', 0.44),
    ('Хлевенский', 0.37),
    ('Чаплыгинский', 0.49)
) AS t(mo_name, score)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_5' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_6: Молодежь в Движении Первых (percentages 0.30-0.55)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, score * 3, NOW(), NOW() FROM (
  VALUES
    ('Липецк', 0.55),
    ('Елец', 0.51),
    ('Воловский', 0.30),
    ('Грязянский', 0.38),
    ('Данковский', 0.34),
    ('Добринский', 0.43),
    ('Добровский', 0.40),
    ('Долгоруковский', 0.52),
    ('Елецкий', 0.31),
    ('Задонский', 0.47),
    ('Измалковский', 0.49),
    ('Краснинский', 0.32),
    ('Лебедянский', 0.44),
    ('Лев-Толстовский', 0.48),
    ('Липецкий', 0.53),
    ('Становлянский', 0.35),
    ('Тербунский', 0.33),
    ('Усманский', 0.46),
    ('Хлевенский', 0.39),
    ('Чаплыгинский', 0.51)
) AS t(mo_name, score)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_6' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_7: Работа с ветеранами СВО (number of meetings)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1,
  CASE
    WHEN meetings >= 36 THEN 3
    WHEN meetings >= 12 THEN 2
    WHEN meetings >= 3 THEN 1
    ELSE 0
  END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 40),
    ('Елец', 38),
    ('Воловский', 25),
    ('Грязянский', 28),
    ('Данковский', 10),
    ('Добринский', 32),
    ('Добровский', 18),
    ('Долгоруковский', 42),
    ('Елецкий', 8),
    ('Задонский', 30),
    ('Измалковский', 35),
    ('Краснинский', 12),
    ('Лебедянский', 22),
    ('Лев-Толстовский', 34),
    ('Липецкий', 39),
    ('Становлянский', 15),
    ('Тербунский', 11),
    ('Усманский', 31),
    ('Хлевенский', 20),
    ('Чаплыгинский', 37)
) AS t(mo_name, meetings)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_7' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_8: Кадровый управленческий резерв (percentages 0.65-0.85 scaled to 3)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1,
  CASE
    WHEN pct >= 0.80 THEN 3
    WHEN pct >= 0.50 THEN 2
    WHEN pct >= 0.30 THEN 1
    ELSE 0
  END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 0.85),
    ('Елец', 0.81),
    ('Воловский', 0.65),
    ('Грязянский', 0.75),
    ('Данковский', 0.55),
    ('Добринский', 0.78),
    ('Добровский', 0.68),
    ('Долгоруковский', 0.82),
    ('Елецкий', 0.58),
    ('Задонский', 0.76),
    ('Измалковский', 0.80),
    ('Краснинский', 0.62),
    ('Лебедянский', 0.70),
    ('Лев-Толстовский', 0.79),
    ('Липецкий', 0.83),
    ('Становлянский', 0.67),
    ('Тербунский', 0.60),
    ('Усманский', 0.77),
    ('Хлевенский', 0.69),
    ('Чаплыгинский', 0.81)
) AS t(mo_name, pct)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_8' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pub_9: Работа с грантами (grant wins 2-5)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1,
  CASE
    WHEN grants >= 3 THEN 3
    WHEN grants >= 1 THEN 1
    ELSE 0
  END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 5),
    ('Елец', 4),
    ('Воловский', 2),
    ('Грязянский', 3),
    ('Данковский', 1),
    ('Добринский', 3),
    ('Добровский', 2),
    ('Долгоруковский', 4),
    ('Елецкий', 0),
    ('Задонский', 3),
    ('Измалковский', 3),
    ('Краснинский', 1),
    ('Лебедянский', 2),
    ('Лев-Толстовский', 3),
    ('Липецкий', 5),
    ('Становлянский', 1),
    ('Тербунский', 1),
    ('Усманский', 2),
    ('Хлевенский', 1),
    ('Чаплыгинский', 4)
) AS t(mo_name, grants)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pub_9' AND i.rating_type = 'ПУБЛИЧНЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_1: Партийное мнение в администрации (raw counts, needs normalization)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, LEAST(6, GREATEST(0, (count::float / 500 * 6)::int)), NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 2150),
    ('Елец', 830),
    ('Воловский', 110),
    ('Грязянский', 550),
    ('Данковский', 180),
    ('Добринский', 620),
    ('Добровский', 200),
    ('Долгоруковский', 700),
    ('Елецкий', 150),
    ('Задонский', 480),
    ('Измалковский', 560),
    ('Краснинский', 220),
    ('Лебедянский', 380),
    ('Лев-Толстовский', 650),
    ('Липецкий', 1900),
    ('Становлянский', 270),
    ('Тербунский', 190),
    ('Усманский', 520),
    ('Хлевенский', 300),
    ('Чаплыгинский', 750)
) AS t(mo_name, count)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_1' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_2: Распределение мандатов (percentages scaled to 4)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, score * 4, NOW(), NOW() FROM (
  VALUES
    ('Липецк', 1.0),
    ('Елец', 0.95),
    ('Воловский', 0.94),
    ('Грязянский', 0.96),
    ('Данковский', 0.88),
    ('Добринский', 0.93),
    ('Добровский', 0.90),
    ('Долгоруковский', 0.97),
    ('Елецкий', 0.85),
    ('Задонский', 0.92),
    ('Измалковский', 0.95),
    ('Краснинский', 0.87),
    ('Лебедянский', 0.91),
    ('Лев-Толстовский', 0.94),
    ('Липецкий', 0.99),
    ('Становлянский', 0.89),
    ('Тербунский', 0.86),
    ('Усманский', 0.93),
    ('Хлевенский', 0.90),
    ('Чаплыгинский', 0.96)
) AS t(mo_name, score)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_2' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_3: Показатели АГП (уровень) - categorical
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, CASE level
  WHEN 'превысил' THEN 5
  WHEN 'выполнен' THEN 3
  ELSE 0
END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 'превысил'),
    ('Елец', 'выполнен'),
    ('Воловский', 'не выполнен'),
    ('Грязянский', 'превысил'),
    ('Данковский', 'выполнен'),
    ('Добринский', 'превысил'),
    ('Добровский', 'выполнен'),
    ('Долгоруковский', 'превысил'),
    ('Елецкий', 'не выполнен'),
    ('Задонский', 'превысил'),
    ('Измалковский', 'превысил'),
    ('Краснинский', 'выполнен'),
    ('Лебедянский', 'выполнен'),
    ('Лев-Толстовский', 'превысил'),
    ('Липецкий', 'превысил'),
    ('Становлянский', 'выполнен'),
    ('Тербунский', 'не выполнен'),
    ('Усманский', 'превысил'),
    ('Хлевенский', 'выполнен'),
    ('Чаплыгинский', 'превысил')
) AS t(mo_name, level)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_3' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_4: Показатели АГП (качество) - categorical
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, CASE quality
  WHEN 'превышает' THEN 5
  WHEN 'достигнут' THEN 3
  ELSE 0
END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 'превышает'),
    ('Елец', 'достигнут'),
    ('Воловский', 'не достигнут'),
    ('Грязянский', 'превышает'),
    ('Данковский', 'достигнут'),
    ('Добринский', 'превышает'),
    ('Добровский', 'достигнут'),
    ('Долгоруковский', 'превышает'),
    ('Елецкий', 'не достигнут'),
    ('Задонский', 'превышает'),
    ('Измалковский', 'превышает'),
    ('Краснинский', 'достигнут'),
    ('Лебедянский', 'достигнут'),
    ('Лев-Толстовский', 'превышает'),
    ('Липецкий', 'превышает'),
    ('Становлянский', 'достигнут'),
    ('Тербунский', 'не достигнут'),
    ('Усманский', 'превышает'),
    ('Хлевенский', 'достигнут'),
    ('Чаплыгинский', 'превышает')
) AS t(mo_name, quality)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_4' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_5: Экономическая привлекательность - categorical
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, CASE attraction
  WHEN 'высокая' THEN 1
  WHEN 'средняя' THEN 2
  ELSE 3
END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 'высокая'),
    ('Елец', 'высокая'),
    ('Воловский', 'слабая'),
    ('Грязянский', 'средняя'),
    ('Данковский', 'слабая'),
    ('Добринский', 'средняя'),
    ('Добровский', 'слабая'),
    ('Долгоруковский', 'высокая'),
    ('Елецкий', 'слабая'),
    ('Задонский', 'средняя'),
    ('Измалковский', 'средняя'),
    ('Краснинский', 'слабая'),
    ('Лебедянский', 'средняя'),
    ('Лев-Толстовский', 'средняя'),
    ('Липецкий', 'высокая'),
    ('Становлянский', 'слабая'),
    ('Тербунский', 'слабая'),
    ('Усманский', 'средняя'),
    ('Хлевенский', 'слабая'),
    ('Чаплыгинский', 'средняя')
) AS t(mo_name, attraction)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_5' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_7: Партийная принадлежность ветеранов (raw counts normalized)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, LEAST(6, GREATEST(0, (count::float / 500 * 6)::int)), NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 1250),
    ('Елец', 480),
    ('Воловский', 60),
    ('Грязянский', 300),
    ('Данковский', 90),
    ('Добринский', 350),
    ('Добровский', 110),
    ('Долгоруковский', 400),
    ('Елецкий', 70),
    ('Задонский', 280),
    ('Измалковский', 320),
    ('Краснинский', 100),
    ('Лебедянский', 210),
    ('Лев-Толстовский', 370),
    ('Липецкий', 1100),
    ('Становлянский', 140),
    ('Тербунский', 95),
    ('Усманский', 290),
    ('Хлевенский', 160),
    ('Чаплыгинский', 420)
) AS t(mo_name, count)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_7' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- closed_8: Участие в проекте "Гордость" (project members count: 0-5)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1,
  CASE
    WHEN members >= 1 THEN 2
    ELSE 0
  END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 5),
    ('Елец', 3),
    ('Воловский', 1),
    ('Грязянский', 2),
    ('Данковский', 0),
    ('Добринский', 2),
    ('Добровский', 1),
    ('Долгоруковский', 3),
    ('Елецкий', 0),
    ('Задонский', 2),
    ('Измалковский', 2),
    ('Краснинский', 1),
    ('Лебедянский', 1),
    ('Лев-Толстовский', 2),
    ('Липецкий', 4),
    ('Становлянский', 1),
    ('Тербунский', 0),
    ('Усманский', 2),
    ('Хлевенский', 1),
    ('Чаплыгинский', 2)
) AS t(mo_name, members)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'closed_8' AND i.rating_type = 'ЗАКРЫТЫЙ'
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- Penalty criteria
-- pen_1: Конфликты с региональной властью (Да/Нет -> 0 or -3)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, CASE conflict WHEN 'Да' THEN -3 ELSE 0 END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 'Нет'),
    ('Елец', 'Нет'),
    ('Воловский', 'Нет'),
    ('Грязянский', 'Нет'),
    ('Данковский', 'Да'),
    ('Добринский', 'Нет'),
    ('Добровский', 'Нет'),
    ('Долгоруковский', 'Нет'),
    ('Елецкий', 'Да'),
    ('Задонский', 'Нет'),
    ('Измалковский', 'Нет'),
    ('Краснинский', 'Нет'),
    ('Лебедянский', 'Нет'),
    ('Лев-Толстовский', 'Нет'),
    ('Липецкий', 'Нет'),
    ('Становлянский', 'Да'),
    ('Тербунский', 'Да'),
    ('Усманский', 'Нет'),
    ('Хлевенский', 'Нет'),
    ('Чаплыгинский', 'Нет')
) AS t(mo_name, conflict)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pen_1' AND i.is_penalty = true
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pen_2: Внутримуниципальные конфликты (numeric: 0-4 -> score calculation)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1,
  CASE
    WHEN conflicts >= 4 THEN -3
    WHEN conflicts > 1 THEN -2
    WHEN conflicts > 0 THEN -1
    ELSE 0
  END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 2),
    ('Елец', 1),
    ('Воловский', 4),
    ('Грязянский', 2),
    ('Данковский', 3),
    ('Добринский', 1),
    ('Добровский', 2),
    ('Долгоруковский', 1),
    ('Елецкий', 5),
    ('Задонский', 1),
    ('Измалковский', 0),
    ('Краснинский', 2),
    ('Лебедянский', 1),
    ('Лев-Толстовский', 0),
    ('Липецкий', 1),
    ('Становлянский', 3),
    ('Тербунский', 4),
    ('Усманский', 1),
    ('Хлевенский', 2),
    ('Чаплыгинский', 0)
) AS t(mo_name, conflicts)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pen_2' AND i.is_penalty = true
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

-- pen_3: Данные правоохранительных органов (Да/Нет -> 0 or -5)
INSERT INTO fact_indicator (mo_id, ind_id, period_id, score, created_at, updated_at)
SELECT m.mo_id, i.ind_id, 1, CASE le_data WHEN 'Да' THEN -5 ELSE 0 END, NOW(), NOW()
FROM (
  VALUES
    ('Липецк', 'Да'),
    ('Елец', 'Нет'),
    ('Воловский', 'Нет'),
    ('Грязянский', 'Нет'),
    ('Данковский', 'Да'),
    ('Добринский', 'Нет'),
    ('Добровский', 'Нет'),
    ('Долгоруковский', 'Нет'),
    ('Елецкий', 'Да'),
    ('Задонский', 'Нет'),
    ('Измалковский', 'Нет'),
    ('Краснинский', 'Да'),
    ('Лебедянский', 'Нет'),
    ('Лев-Толстовский', 'Нет'),
    ('Липецкий', 'Нет'),
    ('Становлянский', 'Да'),
    ('Тербунский', 'Нет'),
    ('Усманский', 'Нет'),
    ('Хлевенский', 'Нет'),
    ('Чаплыгинский', 'Нет')
) AS t(mo_name, le_data)
JOIN dim_mo m ON m.mo_name = t.mo_name
JOIN dim_indicator i ON i.code = 'pen_3' AND i.is_penalty = true
WHERE NOT EXISTS (
  SELECT 1 FROM fact_indicator f
  WHERE f.mo_id = m.mo_id AND f.ind_id = i.ind_id AND f.period_id = 1
);

COMMIT;

-- Verify insert results
SELECT 'Data loaded successfully!' as result;

SELECT code, COUNT(*) as count
FROM dim_indicator i
JOIN fact_indicator f ON i.ind_id = f.ind_id
WHERE f.period_id = 1
GROUP BY code
ORDER BY code;
