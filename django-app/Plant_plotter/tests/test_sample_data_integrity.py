import json
import unittest
from collections import Counter
from pathlib import Path


SAMPLE_DATA = (
    Path(__file__).resolve().parents[1]
    / "management"
    / "commands"
    / "sample_data.json"
)

MONTHS = {
    None,
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}

ALLOWED_CATEGORIES = {
    "cover_crop",
    "flower",
    "fruit",
    "herb",
    "ornamental",
    "tree_shrub",
    "vegetable",
    "weed",
    "wildlife_native",
}

ALLOWED_ROLES = {
    "aromatic_pest_confuser",
    "beneficial_insect_plant",
    "cover_crop",
    "edible",
    "flowering",
    "hedgerow",
    "invasive",
    "living_mulch",
    "nitrogen_fixer",
    "ornamental",
    "perennial_plant",
    "pollinator",
    "problem_plant",
    "shrub",
    "soil_improver",
    "trap_crop",
    "tree",
    "weed",
    "wildlife_support",
}

PRODUCTIVE_CATEGORIES = {
    "cover_crop",
    "flower",
    "fruit",
    "herb",
    "vegetable",
    "wildlife_native",
}

AVOID_ONLY_PLANTS = {
    "Florence Fennel",
    "Herb Fennel",
}

EXPECTED_WEEDS = {
    "Annual Meadow Grass",
    "Bindweed",
    "Broad-leaved Dock",
    "Cleavers",
    "Common Chickweed",
    "Couch Grass",
    "Creeping Thistle",
    "Dandelion",
    "Fat Hen",
    "Ground Elder",
    "Hairy Bittercress",
    "Horsetail / Mare's Tail",
    "Japanese Knotweed",
    "Oxalis",
    "Shepherd's Purse",
}


class SampleDataIntegrityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plants = json.loads(SAMPLE_DATA.read_text())["plants"]
        cls.names = [plant["name"] for plant in cls.plants]
        cls.name_set = set(cls.names)

    def test_plant_names_are_unique(self):
        duplicates = [
            name for name, count in Counter(self.names).items() if count > 1
        ]

        self.assertEqual(duplicates, [])

    def test_there_is_only_one_seed_data_source(self):
        sample_files = sorted(
            path.name for path in SAMPLE_DATA.parent.glob("sample_data*.json")
        )

        self.assertEqual(sample_files, ["sample_data.json"])

    def test_plant_labels_are_valid(self):
        bad_categories = []
        bad_roles = []
        bad_role_types = []

        for plant in self.plants:
            category = plant.get("plant_category")
            roles = plant.get("plant_roles")

            if category not in ALLOWED_CATEGORIES:
                bad_categories.append((plant["name"], category))
            if not isinstance(roles, list):
                bad_role_types.append((plant["name"], type(roles).__name__))
                continue
            for role in roles:
                if role not in ALLOWED_ROLES:
                    bad_roles.append((plant["name"], role))

        self.assertEqual(bad_categories, [])
        self.assertEqual(bad_role_types, [])
        self.assertEqual(bad_roles, [])

    def test_normalised_plant_names_are_unique(self):
        def normalise(name):
            return "".join(char for char in name.lower() if char.isalnum())

        by_normalised_name = {}
        for name in self.names:
            by_normalised_name.setdefault(normalise(name), []).append(name)

        near_duplicates = [
            names for names in by_normalised_name.values() if len(names) > 1
        ]

        self.assertEqual(near_duplicates, [])

    def test_relationship_references_are_valid(self):
        missing = []
        self_references = []

        for plant in self.plants:
            for field in (
                "companion_helps",
                "companion_helped_by",
                "plants_avoid",
            ):
                for other_name in plant.get(field, []):
                    if other_name not in self.name_set:
                        missing.append((plant["name"], field, other_name))
                    if other_name == plant["name"]:
                        self_references.append((plant["name"], field))

        self.assertEqual(missing, [])
        self.assertEqual(self_references, [])

    def test_companion_and_avoid_relationships_are_reciprocal(self):
        helps = {
            (plant["name"], other)
            for plant in self.plants
            for other in plant.get("companion_helps", [])
        }
        helped_by = {
            (plant["name"], other)
            for plant in self.plants
            for other in plant.get("companion_helped_by", [])
        }
        avoids = {
            (plant["name"], other)
            for plant in self.plants
            for other in plant.get("plants_avoid", [])
        }

        companion_issues = []
        for plant_name, other_name in helps:
            if (other_name, plant_name) not in helped_by:
                companion_issues.append((plant_name, "helps", other_name))
        for plant_name, other_name in helped_by:
            if (other_name, plant_name) not in helps:
                companion_issues.append((plant_name, "helped_by", other_name))

        avoid_issues = [
            (plant_name, other_name)
            for plant_name, other_name in avoids
            if (other_name, plant_name) not in avoids
        ]

        self.assertEqual(companion_issues, [])
        self.assertEqual(avoid_issues, [])

    def test_no_pair_is_both_companion_and_avoid(self):
        companion_pairs = {
            frozenset((plant["name"], other))
            for plant in self.plants
            for field in ("companion_helps", "companion_helped_by")
            for other in plant.get(field, [])
        }
        avoid_pairs = {
            frozenset((plant["name"], other))
            for plant in self.plants
            for other in plant.get("plants_avoid", [])
        }

        conflicts = sorted(tuple(pair) for pair in companion_pairs & avoid_pairs)

        self.assertEqual(conflicts, [])

    def test_productive_plants_have_relationship_data(self):
        missing_relationships = [
            plant["name"]
            for plant in self.plants
            if plant.get("plant_category") in PRODUCTIVE_CATEGORIES
            and not plant.get("companion_helps")
            and not plant.get("companion_helped_by")
            and not plant.get("plants_avoid")
        ]

        self.assertEqual(missing_relationships, [])

    def test_productive_plants_have_companions_unless_avoid_only(self):
        missing_companions = [
            plant["name"]
            for plant in self.plants
            if plant.get("plant_category") in PRODUCTIVE_CATEGORIES
            and plant["name"] not in AVOID_ONLY_PLANTS
            and not plant.get("companion_helps")
            and not plant.get("companion_helped_by")
        ]

        self.assertEqual(missing_companions, [])

    def test_weeds_are_labeled_and_not_used_as_companions(self):
        plants_by_name = {plant["name"]: plant for plant in self.plants}
        missing_weeds = sorted(EXPECTED_WEEDS - plants_by_name.keys())
        bad_labels = []
        weed_companions = []

        for name in EXPECTED_WEEDS & plants_by_name.keys():
            plant = plants_by_name[name]
            roles = set(plant.get("plant_roles", []))
            if plant.get("plant_category") != "weed" or not {
                "weed",
                "problem_plant",
            }.issubset(roles):
                bad_labels.append((name, plant.get("plant_category"), roles))

            for field in ("companion_helps", "companion_helped_by"):
                if plant.get(field):
                    weed_companions.append((name, field, plant[field]))

        self.assertEqual(missing_weeds, [])
        self.assertEqual(bad_labels, [])
        self.assertEqual(weed_companions, [])

    def test_spacing_used_by_canvas_is_never_zero(self):
        zero_spacing = [
            plant["name"]
            for plant in self.plants
            if plant["spacing_between_rows"] <= 0 or plant["spacing_in_rows"] <= 0
        ]

        self.assertEqual(zero_spacing, [])

    def test_month_fields_use_known_month_names(self):
        bad_values = []

        for plant in self.plants:
            for field in (
                "plant_start",
                "plant_end",
                "harest_start",
                "harest_end",
                "time_to_germinate_indoors_start",
                "time_to_germinate_indoors_end",
            ):
                if plant.get(field) not in MONTHS:
                    bad_values.append((plant["name"], field, plant.get(field)))

        self.assertEqual(bad_values, [])
