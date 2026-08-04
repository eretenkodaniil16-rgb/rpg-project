from __future__ import annotations

from dataclasses import dataclass
from typing import Final

FPS: Final[int] = 30
ANIMATION_SECONDS: Final[float] = 15.0
TOTAL_FRAMES: Final[int] = int(FPS * ANIMATION_SECONDS)


@dataclass(frozen=True)
class CardiacPhase:
    index: int
    slug: str
    title_ru: str
    duration_seconds_real: float
    frame_count: int
    description_ru: tuple[str, ...]
    av_valves: str
    semilunar_valves: str
    atrial_contraction: float
    ventricular_contraction: float
    red_flow: str
    blue_flow: str


PHASES: Final[tuple[CardiacPhase, ...]] = (
    CardiacPhase(
        1,
        "atrial_systole",
        "Систола предсердий",
        0.10,
        56,
        (
            "Предсердия сокращаются и нагнетают дополнительный объём крови в желудочки.",
            "Атриовентрикулярные клапаны открыты.",
            "Полулунные клапаны закрыты.",
        ),
        "open",
        "closed",
        1.0,
        0.0,
        "atrium_to_ventricle",
        "atrium_to_ventricle",
    ),
    CardiacPhase(
        2,
        "asynchronous_contraction",
        "Асинхронное сокращение желудочков",
        0.05,
        28,
        (
            "Сокращение распространяется по миокарду желудочков неодновременно.",
            "Давление начинает быстро возрастать.",
            "Атриовентрикулярные клапаны закрываются.",
        ),
        "closing",
        "closed",
        0.0,
        0.45,
        "none",
        "none",
    ),
    CardiacPhase(
        3,
        "isometric_contraction",
        "Изометрическое сокращение",
        0.03,
        17,
        (
            "Все волокна желудочков охвачены сокращением.",
            "Все клапаны закрыты, поэтому объём крови не изменяется.",
            "Напряжение миокарда и давление быстро возрастают.",
        ),
        "closed",
        "closed",
        0.0,
        0.78,
        "none",
        "none",
    ),
    CardiacPhase(
        4,
        "rapid_ejection",
        "Быстрое изгнание",
        0.12,
        68,
        (
            "Давление в желудочках превышает давление в аорте и лёгочном стволе.",
            "Полулунные клапаны открываются.",
            "Кровь быстро выбрасывается в сосуды.",
        ),
        "closed",
        "open",
        0.0,
        1.0,
        "ventricle_to_aorta_fast",
        "ventricle_to_pulmonary_fast",
    ),
    CardiacPhase(
        5,
        "slow_ejection",
        "Медленное изгнание",
        0.13,
        73,
        (
            "Изгнание крови продолжается, но его скорость постепенно снижается.",
            "Полулунные клапаны остаются открытыми.",
            "Предсердия наполняются кровью из вен.",
        ),
        "closed",
        "open",
        0.0,
        0.88,
        "ventricle_to_aorta_slow",
        "ventricle_to_pulmonary_slow",
    ),
    CardiacPhase(
        6,
        "protodiastolic_period",
        "Протодиастолический период",
        0.04,
        22,
        (
            "Начинается расслабление желудочков.",
            "Давление становится ниже давления в аорте и лёгочном стволе.",
            "Кратковременный обратный ток закрывает полулунные клапаны.",
        ),
        "closed",
        "closing",
        0.0,
        0.55,
        "brief_reverse",
        "brief_reverse",
    ),
    CardiacPhase(
        7,
        "isometric_relaxation",
        "Изометрическое расслабление",
        0.08,
        45,
        (
            "Желудочки расслабляются при закрытых клапанах.",
            "Давление быстро снижается.",
            "Объём крови в желудочках остаётся постоянным.",
        ),
        "closed",
        "closed",
        0.0,
        0.20,
        "none",
        "none",
    ),
    CardiacPhase(
        8,
        "rapid_filling",
        "Быстрое наполнение желудочков",
        0.08,
        45,
        (
            "Давление в желудочках становится ниже давления в предсердиях.",
            "Атриовентрикулярные клапаны открываются.",
            "Кровь быстро поступает в желудочки.",
        ),
        "open",
        "closed",
        0.0,
        0.0,
        "atrium_to_ventricle_fast",
        "atrium_to_ventricle_fast",
    ),
    CardiacPhase(
        9,
        "slow_filling",
        "Медленное наполнение",
        0.17,
        96,
        (
            "Пассивное наполнение желудочков продолжается с меньшей скоростью.",
            "Давление в предсердиях и желудочках постепенно выравнивается.",
            "Сердце готовится к следующей систоле предсердий.",
        ),
        "open",
        "closed",
        0.0,
        0.0,
        "atrium_to_ventricle_slow",
        "atrium_to_ventricle_slow",
    ),
)


def phase_ranges() -> tuple[tuple[CardiacPhase, int, int], ...]:
    start = 1
    ranges: list[tuple[CardiacPhase, int, int]] = []
    for phase in PHASES:
        end = start + phase.frame_count - 1
        ranges.append((phase, start, end))
        start = end + 1
    if start - 1 != TOTAL_FRAMES:
        raise AssertionError(
            f"Timeline must contain {TOTAL_FRAMES} frames, got {start - 1}."
        )
    return tuple(ranges)


def validate_phase_data() -> None:
    if len(PHASES) != 9:
        raise AssertionError("The Pokrovsky cardiac-cycle plan must have 9 phases.")
    if sum(phase.frame_count for phase in PHASES) != TOTAL_FRAMES:
        raise AssertionError("Phase frame counts do not sum to the 15-second timeline.")
    if abs(sum(phase.duration_seconds_real for phase in PHASES) - 0.8) > 1e-9:
        raise AssertionError("Real physiological durations must sum to 0.8 seconds.")
    indices = tuple(phase.index for phase in PHASES)
    if indices != tuple(range(1, 10)):
        raise AssertionError("Phase indices must be consecutive from 1 to 9.")


validate_phase_data()
