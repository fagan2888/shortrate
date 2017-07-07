# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  sonntagsgesicht <sonntagsgesicht@github.com>
#  Website: https://github.com/sonntagsgesicht/shortrate
#  License: MIT (see LICENSE file)

from math import sqrt, exp, log

from dcf import ZeroRateCurve, FxCurve

from risk_factor_model import RiskFactorModel
from timewave import GeometricBrownianMotion


class GBMFxCurve(FxCurve, RiskFactorModel):
    """
    models fx spot rate as spot * x
    """

    @classmethod
    def cast(cls, other, volatility=0.0):
        """
        :param FxCurve other: FxCurve to retrieve factor expectation
        :param float or function or Curve volatility: fx rate volatility
        """
        new = cls(volatility=volatility, inner_factor=other)
        return new

    def __init__(self, x_list=None, y_list=None, y_inter=None, origin=None, day_count=None,
                 domestic_curve=None, foreign_curve=None, volatility=0.0, inner_factor=None):
        """

        :param list(BusinessDate) x_list:
        :param list(BusinessDate) y_list:
        :param list() y_inter:
        :param BusinessDate origin:
        :param DayCount day_count:
        :param RateCurve domestic_curve:
        :param RateCurve foreign_curve:
        :param float or function volatility:
        :param FxCurve inner_factor:
        """
        if inner_factor is None:
            inner_factor = FxCurve(x_list, y_list, y_inter, origin, day_count, domestic_curve, foreign_curve)
        else:
            if any([x_list, y_list, y_inter, origin, day_count]):
                raise (TypeError, 'If `inner_factor` is given all other `FxCurve` properties must be `None`.')

        RiskFactorModel.__init__(self, inner_factor, inner_factor.get_fx_rate(inner_factor.origin))

        super(GBMFxCurve, self).__init__(inner_factor.domain,
                                         [inner_factor(x) for x in inner_factor.domain],
                                         (inner_factor._y_left, inner_factor._y_mid, inner_factor._y_right),
                                         inner_factor.origin, inner_factor.day_count,
                                         inner_factor.domestic_curve, inner_factor.foreign_curve)

        # init volatility
        if isinstance(volatility, float):
            self.volatility = (lambda x: volatility)
        elif hasattr(volatility, 'origin'):
            self.volatility = volatility.to_curve()
        else:
            self.volatility = volatility

        self._factor_date = self.origin
        self._factor_value = 1.0

        self._gbm = GeometricBrownianMotion()

    # RiskFactorModel methods

    def evolve(self, x, s, e, q):
        start = self.origin.diff_in_years(s)
        end = self.origin.diff_in_years(e)
        v = log(self.volatility(e) * sqrt(end))
        if start:
            v /= log(self.volatility(s) * sqrt(start))
        return s * self._gbm.evolve(exp(v), start, end, q)

    # FxCurve methods

    def get_fx_rate(self, value_date):
        y = self._factor_value * \
            self.foreign_curve.get_discount_factor(self._factor_date, value_date) / \
            self.domestic_curve.get_discount_factor(self._factor_date, value_date)
        return y


class BrownianZeroRateCurve(ZeroRateCurve, RiskFactorModel):
    """
        simple Brownian motion rate diffusion
    """

    @classmethod
    def cast(cls, other, drift=0.0, volatility=0.0):
        new = cls(drift=drift, volatility=volatility, inner_factor=other)
        return new

    def __init__(self, x_list=None, y_list=None, y_inter=None,
                 origin=None, day_count=None, forward_tenor=None,
                 drift=0.0, volatility=0.0, inner_factor=None):
        """
        initializes Hull White curve

        :param list(float) x_list:
        :param list(float) y_list:
        :param list(interpolation) y_inter:
        :param BusinessDate origin:
        :param DayCount day_count:
        :param BusinessPeriod forward_tenor:
        :param float or function drift:
        :param float or function volatility:
        :param RateCurve inner_factor:
        """
        if inner_factor is None:
            inner_factor = ZeroRateCurve(x_list, y_list, y_inter, origin, day_count, forward_tenor)
        else:
            if any([x_list, y_list, y_inter, origin, day_count, forward_tenor]):
                raise (TypeError, 'If `inner_factor` is given all other `RateCurve` properties must be `None`.')

        RiskFactorModel.__init__(self, inner_factor, 0.0)

        super(BrownianZeroRateCurve, self).__init__(inner_factor.domain,
                                                    [inner_factor.get_storage_type(x) for x in inner_factor.domain],
                                                    (inner_factor._y_left, inner_factor._y_mid, inner_factor._y_right),
                                                    inner_factor.origin, inner_factor.day_count,
                                                    inner_factor.forward_tenor)

        # init drift
        if isinstance(drift, float):
            self.drift = (lambda x: drift)
        elif hasattr(drift, 'origin'):
            self.drift = drift.to_curve()
        else:
            self.drift = drift

        # init volatility
        if isinstance(volatility, float):
            self.volatility = (lambda x: volatility)
        elif hasattr(volatility, 'to_curve'):
            self.volatility = volatility.to_curve()
        else:
            self.volatility = volatility

        self._pre_calc_diffusion = dict()
        self._pre_calc_drift = dict()

        # factor state variables
        self._factor_date = self.origin
        self._factor_value = 0.0

    def __call__(self, x):
        if isinstance(x, (tuple, list)):
            return [self(xx) for xx in x]
        return self.get_discount_factor(self.origin, x)

    def _drift(self, x, s, e):
        return self.drift(s) * (e - s)

    def _diffusion(self, x, s, e):
        return self.volatility(s) * sqrt(e - s)

    def evolve(self, x, s, e, q):
        return self._drift(x, s, e) + self._diffusion(x, s, e) * q

    def get_zero_rate(self, start, stop):
        return self.inner_factor.get_zero_rate(start, stop) + self._factor_value
