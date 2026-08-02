# human_warrior_m01 — attack_sword_01 directional cycles v21

## Цель

Расширить утверждённый `attack_sword_01_down v20 pass05` до полного
четырёхнаправленного набора для одноручного и двуручного хвата:

- `down`;
- `left`;
- `right`;
- `up`.

Результат остаётся арт-кандидатом Blender Sprite Factory. Подключение к Godot
runtime выполняется отдельным этапом после ручной проверки.

## Архитектура

`v21` сохраняет локальную механику утверждённого восьмикадрового удара `v20` и
создаёт самостоятельные Action для направлений `left`, `right` и `up`.

Направление формируется реальным поворотом 3D-рига вокруг вертикальной оси и
выбором соответствующего оружейного модуля. Простое отражение PNG, отрицательный
масштаб и перестановка физических сторон экипировки не используются.

Два утверждённых Action направления `down` остаются источником:

```text
attack_sword_01_onehand_down_v20
attack_sword_01_twohand_down_v20
```

Дополнительно создаются шесть Action:

```text
attack_sword_01_onehand_left_v21
attack_sword_01_twohand_left_v21
attack_sword_01_onehand_right_v21
attack_sword_01_twohand_right_v21
attack_sword_01_onehand_up_v21
attack_sword_01_twohand_up_v21
```

## Кадры

Каждый Action содержит восемь фаз:

```text
f01 guard
f02 windup
f03 anticipation
f04 contact
f05 follow_through
f06 rebound
f07 recovery
f08 settle
```

Итого:

- 8 Action;
- 8 кадров на Action;
- 64 PNG;
- 12 FPS;
- non-loop;
- gameplay canvas 96×96;
- baseline `y=91`.

## Оружейные модули

Для одноручного хвата:

- `down` использует утверждённый `onehand_ready v09`;
- `left`, `right` и `up` используют самостоятельные модули v12.

Для двуручного хвата используется `twohand_center_high v06`, отображаемый через
направленную систему v12 при реальном повороте рига.

Геометрия мечей, материалы и длина клинка не меняются.

## Автоматические проверки

Blender workflow проверяет:

- наличие всех 64 кадров;
- размеры 96×96 и baseline `y=91`;
- отсутствие пустых кадров;
- отсутствие alpha-пикселей на границах для новых направлений;
- сохранение специального утверждённого boundary-контракта `down`;
- минимальный зазор оружия от проекции головы;
- положительный масштаб рига;
- отсутствие mirroring и negative scale;
- генерацию общего и четырёх направленных contact sheet;
- manifest и исходный `.blend`.

## Ручная проверка

Перед одобрением необходимо проверить:

1. постоянные физические стороны большого и малого наплечников;
2. стороны ножен, подсумка и меча;
3. читаемость силуэта в реальном размере 96×96;
4. отсутствие визуального входа клинка в голову и корпус;
5. устойчивую базовую линию;
6. плавность перехода `f08 → combat_idle`;
7. отсутствие зеркального ощущения у `left` и `right`.

## Запуск на Windows

```powershell
.\tools\blender_sprite_factory\run_blender_sprite_pilot.ps1 `
  -Stage attack_directional_cycle_v21
```

Проверяемые файлы:

```text
attack_sword_01_directional_cycle_v21.png
attack_sword_01_down_cycle_v21.png
attack_sword_01_left_cycle_v21.png
attack_sword_01_right_cycle_v21.png
attack_sword_01_up_cycle_v21.png
```
