# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  sonntagsgesicht <sonntagsgesicht@github.com>
#  Website: https://github.com/sonntagsgesicht/shortrate
#  License: MIT (see LICENSE file)


__doc__ = 'risk factor model library python style.'
__version__ = '0.3'
__dev_status__ = '3 - Alpha'
__date__ = 'Thursday, 29 August 2019'
__author__ = 'sonntagsgesicht, based on a fork of Deutsche Postbank [pbrisk]'
__email__ = 'sonntagsgesicht@icloud.com'
__url__ = 'https://github.com/sonntagsgesicht/' + __name__
__license__ = 'Apache License 2.0'
__dependencies__ = ('businessdate','timewave','dcf','scipy')
__dependency_links__ = ()
__data__ = ()
__scripts__ = ()

from risk_factor_model import *
from market_risk_factor import *
from hullwhite_model import *
from hullwhite_multicurrency_model import *
