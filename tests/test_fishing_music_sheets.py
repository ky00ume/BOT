import unittest
from player import Player
from fishing import roll_fishing_sheet, FISHING_SHEET_SONGS
from music_system import learned_melodies, equip_score, song_title

class FishingMusicSheetTests(unittest.TestCase):
    def test_forced_drop_unlocks_one_missing_song(self):
        p=Player()
        sid=roll_fishing_sheet(p,rng=lambda:0.0,chooser=lambda xs:xs[0])
        self.assertEqual(sid,FISHING_SHEET_SONGS[0])
        self.assertIn(sid,[k for k,_ in learned_melodies(p)])
        self.assertTrue(equip_score(p,sid)[0])
    def test_no_duplicate_after_both_learned(self):
        p=Player()
        for expected in FISHING_SHEET_SONGS:
            sid=roll_fishing_sheet(p,rng=lambda:0.0,chooser=lambda xs:xs[0])
            self.assertEqual(sid,expected)
        self.assertIsNone(roll_fishing_sheet(p,rng=lambda:0.0,chooser=lambda xs:xs[0]))
    def test_titles(self):
        self.assertEqual(song_title('chiikawa_pajama_parties'),'파자마 파티즈의 노래')
        self.assertEqual(song_title('chiikawa_island_song'),'섬의 노래')

if __name__=='__main__': unittest.main()
