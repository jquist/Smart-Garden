from django.test import SimpleTestCase

from ..solvers.backtracking_solver import pair_relation_score, total_score_grid


class PredefinedScoreTest(SimpleTestCase):
    def setUp(self):
        self.plants = {
            "carrot": {
                "name": "carrot",
                "size": 1,
                "size_same": 1,
                "helps": ["lettuce", "onion"],
                "helps_by": ["lettuce"],
                "avoid": ["dill"],
            },
            "lettuce": {
                "name": "lettuce",
                "size": 1,
                "size_same": 1,
                "helps": ["carrot"],
                "helps_by": ["carrot"],
                "avoid": [],
            },
            "onion": {
                "name": "onion",
                "size": 1,
                "size_same": 1,
                "helps": [],
                "helps_by": [],
                "avoid": [],
            },
            "dill": {
                "name": "dill",
                "size": 1,
                "size_same": 1,
                "helps": [],
                "helps_by": [],
                "avoid": ["carrot"],
            },
            "radish": {
                "name": "radish",
                "size": 1,
                "size_same": 1,
                "helps": [],
                "helps_by": [],
                "avoid": [],
            },
        }

    def test_pair_relation_score_uses_expected_values(self):
        self.assertEqual(pair_relation_score(self.plants, "carrot", "lettuce"), 2)
        self.assertEqual(pair_relation_score(self.plants, "carrot", "onion"), 1)
        self.assertEqual(pair_relation_score(self.plants, "carrot", "radish"), 0)
        self.assertEqual(pair_relation_score(self.plants, "carrot", "dill"), -1000)
        self.assertEqual(pair_relation_score(self.plants, "dill", "carrot"), -1000)

    def test_companion_overlap_scores_higher_than_separate_layout(self):
        companion_overlap_grid = [
            [["carrot", "lettuce"], ""],
        ]

        separate_grid = [
            ["carrot", "lettuce"],
        ]

        companion_score = total_score_grid(
            self.plants,
            companion_overlap_grid,
            avoid=True,
            next_to=False,
        )

        separate_score = total_score_grid(
            self.plants,
            separate_grid,
            avoid=True,
            next_to=False,
        )

        self.assertGreater(companion_score, separate_score)

    def test_avoid_overlap_scores_lower_than_separate_layout(self):
        avoid_overlap_grid = [
            [["carrot", "dill"], ""],
        ]

        separate_grid = [
            ["carrot", "dill"],
        ]

        avoid_score = total_score_grid(
            self.plants,
            avoid_overlap_grid,
            avoid=True,
            next_to=False,
        )

        separate_score = total_score_grid(
            self.plants,
            separate_grid,
            avoid=True,
            next_to=False,
        )

        self.assertLess(avoid_score, separate_score)

    def test_same_type_next_to_reward_increases_score(self):
        next_to_grid = [
            ["carrot", "carrot"],
        ]

        separated_grid = [
            ["carrot", ""],
            ["", "carrot"],
        ]

        next_to_score = total_score_grid(
            self.plants,
            next_to_grid,
            avoid=True,
            next_to=True,
        )

        separated_score = total_score_grid(
            self.plants,
            separated_grid,
            avoid=True,
            next_to=True,
        )

        self.assertGreater(next_to_score, separated_score)