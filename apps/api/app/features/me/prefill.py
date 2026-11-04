"""Pre-fill suggestions from user types (Plan 9 Task 2, ruling P9-R9). Pure: no I/O.

Turns the user's types and follow-up answers into *suggested* changes to the account
holder's own member. Nothing here writes anything: the client shows the suggestions on a
review screen and sends only the ones the user confirms to `PATCH /v1/members/{id}`, which
keeps its own `health_data` check.

Safety rules:
- Only adds. A suggested list is the current list plus what is new; nothing is removed.
- Never relaxes a diet: `diet` is suggested only while the member is on the default
  `non_veg`.
- Only these fields: conditions, allergens, diet, goal, custom_alerts. Never another member.
- Never a goal the members API cannot save (`GoalIn`).
- Weight loss together with gym "build muscle" is a goal conflict: no goal change, the user
  picks one or neither (`goal_choice`).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import get_args

from app.features.me.schemas import FollowUps, PrefillChange, PrefillField, UserType
from app.features.members.schemas import GoalIn, goal_allowed_at_age

DEFAULT_DIET = "non_veg"
# The goal each gym follow-up suggests.
GYM_GOAL_TO_GOAL: dict[str, str] = {
    "build_muscle": "build_muscle",
    "lose_fat": "weight_loss",
    "stay_fit": "healthy_eating",
}
# The two goals of the weight-loss-and-build-muscle conflict, in the order offered.
CONFLICT_GOALS: tuple[str, str] = ("weight_loss", "build_muscle")
_FIELD_ORDER: tuple[PrefillField, ...] = get_args(PrefillField)


def _saveable_goals() -> frozenset[str]:
    """Goals `PATCH /v1/members/{id}` accepts. Read at call time, so `build_muscle` is offered
    as soon as the members API accepts it (Plan 9 Task 3)."""
    return frozenset(get_args(GoalIn))


@dataclass(frozen=True, slots=True)
class MemberSnapshot:
    """The primary member's current values for the fields pre-fill may touch."""

    conditions: tuple[str, ...] = ()
    allergens: tuple[str, ...] = ()
    diet: str = DEFAULT_DIET
    goal: str | None = None
    custom_alerts: tuple[str, ...] = ()
    # The youngest age the birth year allows (`members.service.youngest_age`); None = unknown.
    age: int | None = None


def _union(
    field: PrefillField,
    current: Sequence[str],
    chosen: Sequence[str],
    reason: UserType,
    *,
    casefold: bool = False,
) -> PrefillChange | None:
    """current ∪ chosen (current order first), or None when nothing is new."""

    def key(value: str) -> str:
        return value.casefold() if casefold else value

    have = {key(v) for v in current}
    added: list[str] = []
    for value in chosen:
        if key(value) not in have:
            have.add(key(value))
            added.append(value)
    if not added:
        return None
    return PrefillChange(
        field=field,
        current=list(current),
        value=[*current, *added],
        added=added,
        reason=reason,
    )


def _goal(
    types: Sequence[UserType], follow_ups: FollowUps, current: str | None, age: int | None
) -> tuple[PrefillChange | None, list[str] | None]:
    # P9 safety S4: an adult-only goal (build_muscle) is never offered to a minor.
    saveable = frozenset(g for g in _saveable_goals() if goal_allowed_at_age(g, age))
    gym_goal = (
        GYM_GOAL_TO_GOAL[follow_ups.gym_goal]
        if "gym" in types and follow_ups.gym_goal is not None
        else None
    )
    if "weight_loss" in types and gym_goal == "build_muscle":
        # A conflict: never pick for the user. Offered only when both goals can be saved and
        # the member doesn't already hold one of them (then the user has already chosen).
        if set(CONFLICT_GOALS) <= saveable and current not in CONFLICT_GOALS:
            return None, list(CONFLICT_GOALS)
        return None, None

    suggestion: tuple[str, UserType] | None = None
    if "weight_loss" in types:
        suggestion = ("weight_loss", "weight_loss")
    elif gym_goal is not None:
        suggestion = (gym_goal, "gym")
    elif "eat_better" in types and follow_ups.alerts and current is None:
        suggestion = ("healthy_eating", "eat_better")
    if suggestion is None:
        return None, None
    value, reason = suggestion
    if value == current or value not in saveable:
        return None, None
    return PrefillChange(field="goal", current=current, value=value, added=[], reason=reason), None


def suggest_prefill(
    types: Sequence[UserType], follow_ups: FollowUps, primary: MemberSnapshot
) -> tuple[list[PrefillChange], list[GoalIn] | None]:
    """The suggested changes (in `PrefillField` order) and, on a goal conflict, the goals to
    choose from. ([], None) means nothing to confirm."""
    changes: list[PrefillChange | None] = []
    if "health_condition" in types and follow_ups.conditions:
        changes.append(
            _union("conditions", primary.conditions, follow_ups.conditions, "health_condition")
        )
    if "allergy_diet" in types:
        if follow_ups.allergens:
            changes.append(
                _union(
                    "allergens",
                    primary.allergens,
                    follow_ups.allergens,
                    "allergy_diet",
                    casefold=True,
                )
            )
        diet = follow_ups.diet
        if diet is not None and primary.diet == DEFAULT_DIET and diet != DEFAULT_DIET:
            changes.append(
                PrefillChange(
                    field="diet", current=primary.diet, value=diet, added=[], reason="allergy_diet"
                )
            )
    goal_change, goal_choice = _goal(types, follow_ups, primary.goal, primary.age)
    changes.append(goal_change)
    if "eat_better" in types and follow_ups.alerts:
        changes.append(
            _union("custom_alerts", primary.custom_alerts, follow_ups.alerts, "eat_better")
        )
    out = sorted((c for c in changes if c is not None), key=lambda c: _FIELD_ORDER.index(c.field))
    return out, goal_choice  # type: ignore[return-value]
