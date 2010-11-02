#!/usr/bin/env python
import random
import unittest

import playlist


class PlaylistTest(unittest.TestCase):

  def setUp(self):
    self.pl = playlist.Playlist()

  def tearDown(self):
    del self.pl

  def test_empty(self):
    self.assertEqual(True, self.pl.empty())
    self.pl.items.append(object())
    self.assertEqual(False, self.pl.empty())

  def test_has_multiple(self):
    self.assertEqual(False, self.pl.has_multiple())
    self.pl.items.append(object())
    self.assertEqual(False, self.pl.has_multiple())
    self.pl.items.append(object())
    self.assertEqual(True, self.pl.has_multiple())

  def test_advance(self):
    a = object()
    b = object()
    c = object()
    self.pl.items.append(a)
    self.pl.items.append(b)
    self.pl.items.append(c)
    self.assertEqual([a,b,c], self.pl.items)
    self.pl.advance()
    self.assertEqual([b,c,a], self.pl.items)
    self.pl.advance()
    self.assertEqual([c,a,b], self.pl.items)

  def test_rewind(self):
    a = object()
    b = object()
    c = object()
    self.pl.items.append(a)
    self.pl.items.append(b)
    self.pl.items.append(c)
    self.assertEqual([a,b,c], self.pl.items)
    self.pl.rewind()
    self.assertEqual([c,a,b], self.pl.items)
    self.pl.rewind()
    self.assertEqual([b,c,a], self.pl.items)

  def test_purge(self):
    self.assertEqual(self.pl.items, [])
    a = object()
    b = object()
    c = object()
    self.pl.items.append(a)
    self.pl.items.append(b)
    self.pl.items.append(c)
    self.assertEqual(self.pl.items, [a,b,c])
    self.pl.purge()
    self.assertEqual(self.pl.items, [])

if __name__ == '__main__':
    unittest.main()
