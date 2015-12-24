# -*- coding: utf-8 -*-
"""
    trytonacs_party_access_control_isonas

    :copyright: (c) The file COPYRIGHT at the top level of this
    :repository contains the full copyright notices.
    :license: , see LICENSE for more details.
"""
import unittest
from .test_party import PartyTestCase
import trytond.tests.test_tryton


def suite():
    """
    Define suite
    """
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(PartyTestCase),
    ])
    return test_suite
