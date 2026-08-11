"""Timeline and educational metadata for the 45 s chemical synapse animation."""

from __future__ import annotations

FPS = 30
DURATION_SECONDS = 45
TOTAL_FRAMES = FPS * DURATION_SECONDS
RESOLUTION_X = 1920
RESOLUTION_Y = 1080

PHASES = (
    {
        "id": "rest",
        "title": "1. Состояние покоя",
        "start_s": 0.0,
        "end_s": 4.0,
        "caption": "Синаптические везикулы заполнены медиатором.\nПотенциалзависимые Ca²⁺-каналы закрыты.",
    },
    {
        "id": "action_potential",
        "title": "2. Приход потенциала действия",
        "start_s": 4.0,
        "end_s": 8.0,
        "caption": "Деполяризация достигает пресинаптической терминали\nи изменяет состояние мембраны.",
    },
    {
        "id": "calcium_entry",
        "title": "3. Вход Ca²⁺",
        "start_s": 8.0,
        "end_s": 13.0,
        "caption": "Открываются потенциалзависимые Ca²⁺-каналы;\nCa²⁺ входит в пресинаптическое окончание.",
    },
    {
        "id": "docking_fusion",
        "title": "4. Докинг и слияние везикулы",
        "start_s": 13.0,
        "end_s": 19.0,
        "caption": "Повышение внутриклеточного Ca²⁺ запускает Ca²⁺-зависимое слияние\nподготовленной везикулы с активной зоной.",
    },
    {
        "id": "exocytosis",
        "title": "5. Экзоцитоз нейромедиатора",
        "start_s": 19.0,
        "end_s": 24.0,
        "caption": "Формируется пора слияния, и квант нейромедиатора\nвысвобождается в синаптическую щель.",
    },
    {
        "id": "diffusion_binding",
        "title": "6. Диффузия и связывание",
        "start_s": 24.0,
        "end_s": 31.0,
        "caption": "Молекулы медиатора диффундируют через щель\nи связываются с постсинаптическими рецепторами.",
    },
    {
        "id": "postsynaptic_response",
        "title": "7. Постсинаптический ответ",
        "start_s": 31.0,
        "end_s": 36.0,
        "caption": "Ионотропный путь меняет ионную проводимость;\nметаботропный путь запускает систему вторичных посредников.",
    },
    {
        "id": "clearance",
        "title": "8. Прекращение действия медиатора",
        "start_s": 36.0,
        "end_s": 41.0,
        "caption": "Медиатор удаляется обратным захватом, ферментативным расщеплением\nи диффузией из синаптической щели.",
    },
    {
        "id": "recovery",
        "title": "9. Восстановление",
        "start_s": 41.0,
        "end_s": 45.0,
        "caption": "Ca²⁺ удаляется из терминали, мембрана везикулы рециклируется;\nсинапс возвращается к исходному состоянию.",
    },
)

SOURCE_NOTE = (
    "Учебная схема химической синаптической передачи.\n"
    "Финальные формулировки титров сверяются с Покровским и Guyton & Hall."
)


def sec_to_frame(seconds: float) -> int:
    """Convert timeline seconds to a 1-based Blender frame."""
    frame = int(round(seconds * FPS)) + 1
    return max(1, min(TOTAL_FRAMES, frame))


def phase_for_second(second: float) -> dict:
    """Return phase metadata for a timeline second."""
    if second <= 0:
        return PHASES[0]
    if second >= DURATION_SECONDS:
        return PHASES[-1]
    for phase in PHASES:
        if phase["start_s"] <= second < phase["end_s"]:
            return phase
    return PHASES[-1]


def validate_timeline() -> None:
    assert FPS == 30
    assert DURATION_SECONDS == 45
    assert TOTAL_FRAMES == 1350
    assert PHASES[0]["start_s"] == 0.0
    assert PHASES[-1]["end_s"] == float(DURATION_SECONDS)
    previous_end = 0.0
    for phase in PHASES:
        assert phase["start_s"] == previous_end
        assert phase["end_s"] > phase["start_s"]
        previous_end = phase["end_s"]


validate_timeline()
