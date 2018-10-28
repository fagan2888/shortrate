# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  sonntagsgesicht <sonntagsgesicht@github.com>
#  Website: https://github.com/sonntagsgesicht/shortrate
#  License: MIT (see LICENSE file)

from scipy import integrate

from dcf import DateCurve, ZeroRateCurve, Price, FxRate

from risk_factor_model import RiskFactorModel
from timewave import TimeDependentWienerProcess, TimeDependentGeometricBrownianMotion


class GaussRiskFactorModel(RiskFactorModel, TimeDependentWienerProcess):
    @property
    def drift(self):
        return self._mu

    @property
    def volatility(self):
        return self._sigma

    def __init__(self, inner_factor, mu=0.0, sigma=0.0, time=.0027378507871321013, start=0.0):
        # super(GaussRiskFactorModel, self).__init__()
        RiskFactorModel.__init__(self, inner_factor=inner_factor, start=start)
        TimeDependentWienerProcess.__init__(self, mu=mu, sigma=sigma, time=time, start=start)

        # re-init RiskFactor properties due to funny calls of __init__ in __mro__
        self._inner_factor = inner_factor
        self._factor_value = self.start
        self._factor_date = self._initial_factor_date

    # TimeDependentWienerProcess methods

    def _integrate(self, f, s, e):
        result, _ = integrate.quad(f, s, e)
        return result


class GeometricBrownianMotionRiskFactorModel(GaussRiskFactorModel, TimeDependentGeometricBrownianMotion):
    pass


class GeometricBrownianMotionPriceFactorModel(Price, GeometricBrownianMotionRiskFactorModel):

    @property
    def value(self):
        return self._factor_value

    @property
    def origin(self):
        return self._factor_date

    def __init__(self, inner_factor, drift=0.0, volatility=0.0):
        Price.__init__(self, inner_factor.value, inner_factor.origin, inner_factor.day_count)
        GeometricBrownianMotionRiskFactorModel.__init__(self, inner_factor, drift, volatility, start=inner_factor.value)


class GeometricBrownianMotionPrice(GeometricBrownianMotionPriceFactorModel):
    def __init__(self, value=0.0, origin=None, day_count=None, drift=0.0, volatility=0.0):
        inner_factor = Price(value, origin, day_count)
        super(GeometricBrownianMotionPrice, self).__init__(inner_factor, drift, volatility)


class GeometricBrownianMotionFxRateFactorModel(FxRate, GeometricBrownianMotionRiskFactorModel):

    @property
    def value(self):
        return self._factor_value

    @property
    def origin(self):
        return self._factor_date

    def __init__(self, inner_factor, domestic_curve=None, foreign_curve=None, volatility=0.0):
        domestic_curve = ZeroRateCurve([inner_factor.origin], [0.]) if domestic_curve is None else domestic_curve
        foreign_curve = domestic_curve if foreign_curve is None else foreign_curve

        diff_curve = foreign_curve.cast(ZeroRateCurve) - domestic_curve.cast(ZeroRateCurve)
        domain = diff_curve.domain
        data = list(diff_curve.derivative(d) for d in domain)
        drift = DateCurve(domain, data, origin=inner_factor.origin, day_count=inner_factor.day_count).to_curve()

        FxRate.__init__(self, inner_factor.value, inner_factor.origin, inner_factor.day_count)
        GeometricBrownianMotionRiskFactorModel.__init__(self, inner_factor, drift, volatility, start=inner_factor.value)


class GeometricBrownianMotionFxRate(GeometricBrownianMotionFxRateFactorModel):
    def __init__(self, value=1.0, origin=None, day_count=None, domestic_curve=None, foreign_curve=None, volatility=0.0):
        inner_factor = FxRate(value, origin, day_count)
        super(GeometricBrownianMotionFxRate, self).__init__(inner_factor, domestic_curve, foreign_curve, volatility)


class GaussFlatSpreadZeroRateCurveFactorModel(ZeroRateCurve, GaussRiskFactorModel):
    def __init__(self, inner_factor, drift=0.0, volatility=0.0):
        GaussRiskFactorModel.__init__(self, inner_factor, drift, volatility, start=0.0)
        ZeroRateCurve.__init__(self, inner_factor.domain, inner_factor(inner_factor.domain), inner_factor.interpolation,
                               inner_factor.origin, inner_factor.day_count, inner_factor.forward_tenor)

    def __call__(self, x):
        if isinstance(x, (tuple, list)):
            return [self(xx) for xx in x]
        return self._get_compounding_rate(self.origin, x)

    def _get_compounding_rate(self, start, stop):
        return self.inner_factor.get_zero_rate(start, stop) + self._factor_value


class GaussFlatSpreadZeroRateCurve(GaussFlatSpreadZeroRateCurveFactorModel):
    """ simple Brownian motion rate diffusion """

    def __init__(self, domain=None, data=None, interpolation=None,
                 origin=None, day_count=None, forward_tenor=None,
                 drift=0.0, volatility=0.0):
        inner_factor = ZeroRateCurve(domain, data, interpolation, origin, day_count, forward_tenor)
        super(GaussFlatSpreadZeroRateCurve, self).__init__(inner_factor, drift, volatility)
