import unittest
from types import SimpleNamespace
from cooking_db import cooking_target_ratios,cooking_initial_ratios,cooking_score,food_affinity_modifier,record_food_quality,peek_food_quality,pop_food_quality

class CookingGaugeTests(unittest.TestCase):
    def test_ratios_sum_to_100(self):
        for rid in ("ck_soup_01","steamed_salmon","eel_special"):
            self.assertEqual(sum(cooking_target_ratios(rid).values()),100)
            self.assertEqual(sum(cooking_initial_ratios(rid).values()),100)
    def test_exact_target_scores_100(self):
        self.assertEqual(cooking_score("ck_soup_01",cooking_target_ratios("ck_soup_01")),100)
    def test_two_ingredient_without_secret_is_capped(self):
        initial=cooking_initial_ratios("ck_soup_01")
        self.assertEqual(initial.get("salt"),0)
        self.assertLessEqual(cooking_score("ck_soup_01",initial),90)
    def test_correct_third_ingredient_beats_wrong_one(self):
        correct={"water":45,"herb":45,"salt":10}
        wrong={"water":45,"herb":45,"pepper":10}
        self.assertEqual(cooking_score("ck_soup_01",correct),100)
        self.assertGreater(cooking_score("ck_soup_01",correct),cooking_score("ck_soup_01",wrong))
    def test_affinity_thresholds(self):
        self.assertGreater(food_affinity_modifier(95),0)
        self.assertLess(food_affinity_modifier(15),0)
        self.assertEqual(food_affinity_modifier(60),0)
    def test_food_quality_queue(self):
        p=SimpleNamespace(_flags={})
        record_food_quality(p,"dish",92);record_food_quality(p,"dish",31)
        self.assertEqual(peek_food_quality(p,"dish"),92)
        self.assertEqual(pop_food_quality(p,"dish"),92)
        self.assertEqual(pop_food_quality(p,"dish"),31)

if __name__ == "__main__": unittest.main()
