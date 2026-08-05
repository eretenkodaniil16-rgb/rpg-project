# human_warrior_m01 — approved gameplay atlases v01

Все атласы используют ячейку `96×96`, baseline `y=91`, порядок строк
`down / left / right / up`, бинарный alpha и Nearest-фильтрацию в Godot.

## Наборы

- `human_warrior_m01_idle_v01.png` — `1 × 4`;
- `human_warrior_m01_walk_v01.png` — `6 × 4`;
- `human_warrior_m01_combat_idle_onehand_v01.png` — `4 × 4`;
- `human_warrior_m01_combat_idle_twohand_v01.png` — `4 × 4`;
- `human_warrior_m01_walk_onehand_v01.png` — `6 × 4`;
- `human_warrior_m01_walk_twohand_v01.png` — `6 × 4`;
- `human_warrior_m01_attack_sword_01_onehand_v01.png` — `8 × 4`;
- `human_warrior_m01_attack_sword_01_twohand_v01.png` — `8 × 4`;
- `human_warrior_m01_hit_01_onehand_v01.png` — `6 × 4`;
- `human_warrior_m01_hit_01_twohand_v01.png` — `6 × 4`.

Столбцы attack-атласов: `f01–f08`. Столбцы hit-атласов:
`impact / recoil_peak / release_mid / recovery / settle / guard`.

## Runtime

Attack и hit подключаются через общий
`HumanWarriorAnimationLibrary`. Hit запускается только после фактически
применённого ненулевого урона и не запускается при переходе к 0 HP или смерти.
Для неподдерживаемого оружия и внешнего вида сохраняется процедурный fallback.

## Происхождение

Ресурсы художественно утверждены и сохранены в Git как стабильная основа.
Workflow run, artifact ID, SHA-256 атласов и кадров зафиксированы в:

- `data/visuals/human_warrior_m01_animation_assets_v01.json`;
- `data/visuals/human_warrior_m01_animation_assets_v01.lock.json`.
