"""Plan 9 Task 2: pre-fill suggestions (pure; ruling P9-R9).

Pre-fill only suggests changes to the account holder's own member. It never removes a
condition, allergen or alert, never relaxes a diet, and never suggests a value the members
API could not save.
"""

from typing import get_args

import pytest

from app.features.me.prefill import MemberSnapshot, suggest_prefill
from app.features.me.schemas import FollowUps
from app.features.members.schemas import GoalIn

EMPTY = MemberSnapshot()


def _by_field(changes):
    return {c.field: c for c in changes}


def _one(changes):
    assert len(changes) == 1, changes
    return changes[0]


# --- one test per table row -------------------------------------------------------------------


def test_health_condition_adds_conditions():
    primary = MemberSnapshot(conditions=("hypertension",))
    changes, choice = suggest_prefill(
        ["health_condition"], FollowUps(conditions=["diabetes", "hypertension"]), primary
    )
    c = _one(changes)
    assert (c.field, c.current, c.value, c.added, c.reason) == (
        "conditions",
        ["hypertension"],
        ["hypertension", "diabetes"],
        ["diabetes"],
        "health_condition",
    )
    assert choice is None


def test_health_condition_without_follow_up_suggests_nothing():
    assert suggest_prefill(["health_condition"], FollowUps(), EMPTY) == ([], None)


def test_weight_loss_sets_goal():
    c = _one(suggest_prefill(["weight_loss"], FollowUps(), EMPTY)[0])
    assert (c.field, c.current, c.value, c.added, c.reason) == (
        "goal",
        None,
        "weight_loss",
        [],
        "weight_loss",
    )


def test_weight_loss_when_goal_already_weight_loss_suggests_nothing():
    primary = MemberSnapshot(goal="weight_loss")
    assert suggest_prefill(["weight_loss"], FollowUps(), primary) == ([], None)


@pytest.mark.parametrize(
    ("gym_goal", "goal"),
    [
        ("build_muscle", "build_muscle"),
        ("lose_fat", "weight_loss"),
        ("stay_fit", "healthy_eating"),
    ],
)
def test_gym_goal_maps_to_member_goal(gym_goal, goal):
    primary = MemberSnapshot(goal="weight_gain")
    c = _one(suggest_prefill(["gym"], FollowUps(gym_goal=gym_goal), primary)[0])
    assert (c.field, c.current, c.value, c.added, c.reason) == (
        "goal",
        "weight_gain",
        goal,
        [],
        "gym",
    )


def test_gym_goal_same_as_current_suggests_nothing():
    primary = MemberSnapshot(goal="healthy_eating")
    assert suggest_prefill(["gym"], FollowUps(gym_goal="stay_fit"), primary) == ([], None)


def test_gym_without_follow_up_suggests_nothing():
    assert suggest_prefill(["gym"], FollowUps(), EMPTY) == ([], None)


def test_goal_conflict_offers_choice():
    changes, choice = suggest_prefill(
        ["weight_loss", "gym"], FollowUps(gym_goal="build_muscle"), EMPTY
    )
    assert changes == []  # no goal change: the user picks
    assert choice == ["weight_loss", "build_muscle"]


@pytest.mark.parametrize("current", ["weight_loss", "build_muscle"])
def test_goal_conflict_already_resolved_offers_nothing(current):
    # The user already holds one of the two goals (e.g. picked it on the review screen):
    # nothing to confirm, so the review screen is skipped.
    primary = MemberSnapshot(goal=current)
    changes, choice = suggest_prefill(
        ["gym", "weight_loss"], FollowUps(gym_goal="build_muscle"), primary
    )
    assert (changes, choice) == ([], None)


def test_goal_conflict_never_suggests_an_unsaveable_goal():
    changes, choice = suggest_prefill(
        ["weight_loss", "gym"], FollowUps(gym_goal="build_muscle"), EMPTY
    )
    assert all(c.field != "goal" for c in changes)
    saveable = set(get_args(GoalIn))
    assert choice is None or set(choice) <= saveable


def test_weight_loss_and_lose_fat_is_one_goal_change():
    c = _one(suggest_prefill(["weight_loss", "gym"], FollowUps(gym_goal="lose_fat"), EMPTY)[0])
    assert (c.field, c.value, c.reason) == ("goal", "weight_loss", "weight_loss")


def test_weight_loss_wins_over_stay_fit():
    changes, choice = suggest_prefill(["gym", "weight_loss"], FollowUps(gym_goal="stay_fit"), EMPTY)
    c = _one(changes)
    assert (c.field, c.value, c.reason) == ("goal", "weight_loss", "weight_loss")
    assert choice is None


def test_allergy_diet_adds_allergens():
    primary = MemberSnapshot(allergens=("kiwi",))
    c = _one(suggest_prefill(["allergy_diet"], FollowUps(allergens=["milk", "peanut"]), primary)[0])
    assert (c.field, c.current, c.value, c.added, c.reason) == (
        "allergens",
        ["kiwi"],
        ["kiwi", "milk", "peanut"],
        ["milk", "peanut"],
        "allergy_diet",
    )


def test_allergy_diet_sets_diet_only_from_non_veg():
    c = _one(suggest_prefill(["allergy_diet"], FollowUps(diet="jain"), EMPTY)[0])
    assert (c.field, c.current, c.value, c.added, c.reason) == (
        "diet",
        "non_veg",
        "jain",
        [],
        "allergy_diet",
    )


def test_eat_better_adds_alerts_and_healthy_eating_when_no_goal():
    primary = MemberSnapshot(custom_alerts=("msg",))
    changes = _by_field(
        suggest_prefill(["eat_better"], FollowUps(alerts=["palm_oil", "msg"]), primary)[0]
    )
    assert set(changes) == {"custom_alerts", "goal"}
    alerts = changes["custom_alerts"]
    assert (alerts.current, alerts.value, alerts.added, alerts.reason) == (
        ["msg"],
        ["msg", "palm_oil"],
        ["palm_oil"],
        "eat_better",
    )
    goal = changes["goal"]
    assert (goal.current, goal.value, goal.reason) == (None, "healthy_eating", "eat_better")


def test_eat_better_keeps_an_existing_goal():
    primary = MemberSnapshot(goal="weight_gain")
    changes = suggest_prefill(["eat_better"], FollowUps(alerts=["maida"]), primary)[0]
    assert [c.field for c in changes] == ["custom_alerts"]


def test_eat_better_without_alerts_suggests_nothing():
    assert suggest_prefill(["eat_better"], FollowUps(), EMPTY) == ([], None)


def test_another_types_goal_beats_eat_better():
    changes = suggest_prefill(
        ["eat_better", "gym"], FollowUps(alerts=["maida"], gym_goal="lose_fat"), EMPTY
    )[0]
    goal = _by_field(changes)["goal"]
    assert (goal.value, goal.reason) == ("weight_loss", "gym")
    assert [c.field for c in changes].count("goal") == 1


# --- safety rules -----------------------------------------------------------------------------


def test_never_removes():
    primary = MemberSnapshot(
        allergens=("peanut",), conditions=("pcos",), custom_alerts=("added_sugar",)
    )
    changes = _by_field(
        suggest_prefill(
            ["allergy_diet", "health_condition", "eat_better"],
            FollowUps(allergens=["milk"], conditions=["diabetes"], alerts=["msg"]),
            primary,
        )[0]
    )
    assert changes["allergens"].value == ["peanut", "milk"]
    assert changes["conditions"].value == ["pcos", "diabetes"]
    assert changes["custom_alerts"].value == ["added_sugar", "msg"]
    for change in changes.values():
        if isinstance(change.current, list):
            assert set(change.current) <= set(change.value)


@pytest.mark.parametrize("current", ["vegan", "jain", "veg", "eggetarian"])
def test_never_relaxes_diet(current):
    primary = MemberSnapshot(diet=current)
    for chosen in ("veg", "vegan", "jain", "eggetarian", "non_veg"):
        changes, _ = suggest_prefill(["allergy_diet"], FollowUps(diet=chosen), primary)
        assert changes == [], (current, chosen)


def test_non_veg_choice_from_non_veg_is_no_change():
    assert suggest_prefill(["allergy_diet"], FollowUps(diet="non_veg"), EMPTY) == ([], None)


def test_nothing_new_means_no_change():
    primary = MemberSnapshot(
        conditions=("diabetes", "pcos"),
        allergens=("milk",),
        diet="vegan",
        goal="weight_loss",
        custom_alerts=("palm_oil",),
    )
    follow_ups = FollowUps(
        conditions=["pcos"], allergens=["milk"], diet="vegan", alerts=["palm_oil"]
    )
    assert suggest_prefill(
        ["health_condition", "allergy_diet", "eat_better"], follow_ups, primary
    ) == ([], None)
    assert suggest_prefill(["weight_loss"], FollowUps(), primary) == ([], None)


def test_allergen_match_is_case_insensitive():
    primary = MemberSnapshot(allergens=("Milk",))
    assert suggest_prefill(["allergy_diet"], FollowUps(allergens=["milk"]), primary) == (
        [],
        None,
    )


@pytest.mark.parametrize(
    "follow_ups",
    [FollowUps(), FollowUps(family_with=["children", "parents"])],
)
def test_family_and_skip_suggest_nothing(follow_ups):
    assert suggest_prefill(["family"], follow_ups, EMPTY) == ([], None)
    assert suggest_prefill([], FollowUps(), EMPTY) == ([], None)


def test_follow_ups_without_their_type_suggest_nothing():
    # The API refuses these (422), but the pure function must not act on them either.
    follow_ups = FollowUps(
        conditions=["diabetes"], allergens=["milk"], diet="veg", alerts=["msg"], gym_goal="lose_fat"
    )
    assert suggest_prefill(["family"], follow_ups, EMPTY) == ([], None)


def test_fields_stay_inside_the_table():
    follow_ups = FollowUps(
        conditions=["diabetes"],
        allergens=["milk"],
        diet="veg",
        alerts=["msg"],
        gym_goal="lose_fat",
        family_with=["children"],
    )
    types = ["health_condition", "allergy_diet", "gym"]
    changes, _ = suggest_prefill(types, follow_ups, EMPTY)
    assert [c.field for c in changes] == ["conditions", "allergens", "diet", "goal"]
    assert all(c.reason in types for c in changes)
