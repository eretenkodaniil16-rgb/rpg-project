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
- `human_warrior_m01_attack_sword_01_twohand_v01.png` — `8 × 4`.

Столбцы attack-атласов: `f01–f08`. Первый и восьмой кадры совпадают для
чистого возврата в боевую стойку.

## Статус

Ресурсы художественно утверждены и сохранены в Git как стабильная основа.
Подключение attack-анимаций к Godot runtime выполняется отдельным этапом;
`runtime_connected=false` в manifest.

Происхождение, workflow run, artifact ID и SHA-256 зафиксированы в
`data/visuals/human_warrior_m01_animation_assets_v01.json`.
