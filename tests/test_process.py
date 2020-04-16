# -*- coding: utf-8 -*-

from os.path import join, dirname
import json
import logging
import unittest
import ztf


class ProcessAvroTestSuite(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    logging.basicConfig(level=logging.INFO)

  def testProcessAvroHandler(self):
    with open(join(dirname(__file__), '../events/ProcessAvro.json'), "r") as f:
      event = json.load(f) 
    ztf.ProcessAvroHandler(event, "")

if __name__ == '__main__':
  unittest.main()
