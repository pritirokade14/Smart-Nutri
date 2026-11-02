import pytest

from app.scoring.config import load_config
from app.scoring.models import Category, Diet, Member, Nutrients, Product


@pytest.fixture(scope="session")
def cfg():
    return load_config()


def _p(name, category, kcal, protein, carbs, sugars, fat, sat, fiber, salt, serving, ingredients, claims):
    return Product(
        name=name,
        category=category,
        per_100g=Nutrients(
            energy_kcal=kcal, protein_g=protein, carbs_g=carbs, sugars_g=sugars,
            fat_g=fat, sat_fat_g=sat, fiber_g=fiber, salt_g=salt,
        ),
        serving_size_g=serving,
        ingredients=ingredients,
        claims=claims,
    )


@pytest.fixture
def sf_biscuit():
    return _p("Sugar Free Biscuit", Category.GENERAL, 450, 8, 72, 2.0, 15, 7, 2, 0.9, 25,
              ("wheat flour (maida)", "maltodextrin", "edible vegetable oil (palm)", "milk solids",
               "raising agent (ins 500(ii))", "salt", "emulsifier (ins 322)"), ("Sugar Free",))


@pytest.fixture
def namkeen():
    return _p("Namkeen", Category.GENERAL, 550, 15, 40, 3, 35, 10, 5, 2.5, 30,
              ("gram flour (besan)", "edible vegetable oil", "peanuts", "salt", "spices",
               "onion powder", "garlic powder"), ())


@pytest.fixture
def curd():
    return _p("Curd", Category.GENERAL, 60, 3.5, 4.7, 4.0, 3.1, 2.0, 0, 0.1, 100,
              ("pasteurised toned milk", "active cultures"), ())


@pytest.fixture
def oats():
    return _p("Oats", Category.GENERAL, 389, 13, 66, 1.0, 7, 1.2, 10.6, 0.01, 40,
              ("whole grain rolled oats",), ("High Protein",))


@pytest.fixture
def cola():
    return _p("Cola", Category.BEVERAGE, 42, 0, 10.6, 10.6, 0, 0, 0, 0, 300,
              ("carbonated water", "sugar", "caffeine"), ())


@pytest.fixture
def water():
    return _p("Water", Category.WATER, 0, 0, 0, 0, 0, 0, 0, 0, 500, ("water",), ())


@pytest.fixture
def no_ingredients():
    return _p("No Ingredients", Category.GENERAL, 400, 5, 60, 10, 15, 5, 2, 1.0, None, (), ())


@pytest.fixture
def diabetic_adult():
    return Member(id="m1", name="Diabetic Adult", age=52, diet=Diet.VEG, conditions=("diabetes",))


@pytest.fixture
def milk_allergic_child():
    return Member(id="m2", name="Milk Allergic Child", age=8, diet=Diet.VEG, allergens=("milk",))


@pytest.fixture
def jain_adult():
    return Member(id="m3", name="Jain Adult", age=40, diet=Diet.JAIN)


@pytest.fixture
def bp_parent():
    return Member(id="m4", name="BP Parent", age=70, conditions=("hypertension",))


@pytest.fixture
def peanut_allergic():
    return Member(id="m5", name="Peanut Allergic", age=30, allergens=("peanut",))


@pytest.fixture
def vegan_adult():
    return Member(id="m6", name="Vegan Adult", age=28, diet=Diet.VEGAN)


@pytest.fixture
def weight_loss_adult():
    return Member(id="m7", name="Weight Loss Adult", age=35, goal="weight_loss")


@pytest.fixture
def infant():
    return Member(id="m8", name="Infant", age=1)


@pytest.fixture
def no_age():
    return Member(id="m9", name="No Age", age=None)
