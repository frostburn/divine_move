import random

from django.test import TestCase
import go_board

class BoardTestCase(TestCase):
    def setUp(self):
        b9 = go_board.Board(9)
        b9.player = random.randint(0, 2**81 - 1) & b9.playing_area
        self.b9 = b9

        b13 = go_board.Board(13)
        b13.player = random.randint(0, 2**169 - 1) & b13.playing_area
        self.b13 = b13

    def test_transformations_9(self):
        p = self.b9.player
        self.b9.mirror_h()
        p = go_board.mirror_h(p, 10)
        self.assertEqual(self.b9.player, p)
        
        self.b9.mirror_v()
        p = go_board.mirror_v(p, 10)
        self.assertEqual(self.b9.player, p)

        self.b9.mirror_d()
        p = go_board.mirror_v(p, 10)
        p = go_board.rotate(p, 10)
        self.assertEqual(self.b9.player, p)

    def test_transformations_13(self):
        p = self.b13.player
        self.b13.mirror_h()
        p = go_board.mirror_h(p, 14)
        self.assertEqual(self.b13.player, p)
        
        self.b13.mirror_v()
        p = go_board.mirror_v(p, 14)
        self.assertEqual(self.b13.player, p)

        self.b13.mirror_d()
        p = go_board.mirror_v(p, 14)
        p = go_board.rotate(p, 14)
        self.assertEqual(self.b13.player, p)
