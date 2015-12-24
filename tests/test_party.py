# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends


class PartyTestCase(unittest.TestCase):
    'Test Party module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('party_access_control_isonas')

    # def test005views(self):
    #    'Test Views'
    #    test_view('party_access_control_isonas')

    def test006depends(self):
        'Test Depends'
        test_depends()
