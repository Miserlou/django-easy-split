# -*- coding: utf-8 -*-
import logging
l = logging.getLogger(__name__)

from django_lean.experiments.significance import chi_square_p_value
from django_lean.experiments.tests.utils import TestCase


class TestSignificance(TestCase):
    def testContingencyTableChiSquareValue(self):
        m = [[36,14],[30,25]]
        chi_square_value, p_value = chi_square_p_value(m)
        self.assertAlmostEqual(3.4176732358550534, chi_square_value)
        self.assertAlmostEqual(p_value, 0.0645018648071)
        
        m = [[10, 292], [15, 271]]
        chi_square_value, p_value = chi_square_p_value(m)
        self.assertAlmostEqual(1.3489283703956751, chi_square_value)
        self.assertAlmostEqual(p_value, 0.24546554792)
        
        m = [[17, 285], [34, 252]]
        chi_square_value, p_value = chi_square_p_value(m)
        self.assertAlmostEqual(7.2646044251357011, chi_square_value)
        self.assertAlmostEqual(p_value, 0.00703267568724)
    
