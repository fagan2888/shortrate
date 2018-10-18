# -*- coding: utf-8 -*-

#  shortrate
#  -----------
#  risk factor model library python style.
#
#  Author:  sonntagsgesicht <sonntagsgesicht@github.com>
#  Website: https://github.com/sonntagsgesicht/shortrate
#  License: MIT (see LICENSE file)


from math import exp

from scipy import integrate

from businessdate import BusinessDate
from dcf import FxRate, ZeroRateCurve
from timewave import TimeDependentParameter

from risk_factor_model import RiskFactorModel
from market_risk_factor import GeometricBrownianMotionFxRateFactorModel
from hullwhite_model import HullWhiteCurveFactorModel, HullWhiteCurve


class HullWhiteFxRateFactorModel(FxRate, RiskFactorModel):

    @property
    def value(self):
        return self._factor_value

    @property
    def origin(self):
        return self._factor_date

    def __init__(self, inner_factor, domestic_hw_curve, foreign_hw_curve, volatility=0.0,
                 domestic_correlation=0., foreign_correlation=0., rate_correlation=0., correlation=None):
        """

        :param GeometricBrownianMotionFxRateFactorModel or FxRate inner_factor: if FxRate, volatility is used
        :param HullWhiteCurveFactorModel domestic_hw_curve:
        :param HullWhiteCurveFactorModel foreign_hw_curve:
        :param float: volatility (optional) Default: either inner_factor.volatility or 0.0
        :param float domestic_correlation: (optional) Default: 0.0
        :param float foreign_correlation: (optional) Default: 0.0
        :param float rate_correlation: (optional) Default: 0.0
        :param dict((RiskFactorModel, RiskFactorModel), float) correlation: (optional)
                                                                            Default: explicit given correlations

        """
        if not isinstance(inner_factor, FxRate):
            names = self.__class__.__name__, FxRate.__name__, inner_factor.__class__.__name__
            raise TypeError('%s requires inner_factor of type %s. %s given.' % names)

        if not isinstance(domestic_hw_curve, HullWhiteCurveFactorModel):
            names = self.__class__.__name__, HullWhiteCurveFactorModel.__name__, domestic_hw_curve.__class__.__name__
            raise TypeError('%s requires curve argument of type %s. %s given.' % names)

        if not isinstance(foreign_hw_curve, HullWhiteCurveFactorModel):
            names = self.__class__.__name__, HullWhiteCurveFactorModel.__name__, foreign_hw_curve.__class__.__name__
            raise TypeError('%s requires curve argument of type %s. %s given.' % names)

        FxRate.__init__(self, inner_factor.value, inner_factor.origin, inner_factor.day_count)
        RiskFactorModel.__init__(self, inner_factor, start=inner_factor.value)

        assert self.origin == domestic_hw_curve.origin == foreign_hw_curve.origin

        if isinstance(correlation, dict):
            # todo: check correlation symmetry
            domestic_correlation = correlation.get((domestic_hw_curve, inner_factor), domestic_correlation)
            foreign_correlation = correlation.get((foreign_hw_curve, inner_factor), foreign_correlation)
            rate_correlation = correlation.get((domestic_hw_curve, foreign_hw_curve), rate_correlation)

            domestic_correlation = correlation.get((inner_factor, domestic_hw_curve), domestic_correlation)
            foreign_correlation = correlation.get((inner_factor, foreign_hw_curve), foreign_correlation)
            rate_correlation = correlation.get((foreign_hw_curve, domestic_hw_curve), rate_correlation)

        self.volatility = getattr(inner_factor, 'volatility', TimeDependentParameter(volatility))

        self.domestic_curve = domestic_hw_curve
        self.foreign_curve = foreign_hw_curve

        self.domestic_correlation = domestic_correlation
        self.foreign_correlation = foreign_correlation
        self.rate_correlation = rate_correlation

        self._pre_calc_diffusion = dict()
        self._pre_calc_drift = dict()

        if isinstance(self.inner_factor, RiskFactorModel):
            self._diffusion_driver = self.domestic_curve, self.inner_factor, self.foreign_curve
        else:
            self._diffusion_driver = self.domestic_curve, self, self.foreign_curve

    # integrate drift and diffusion integrals

    def _calc_drift_integrals(self, s, e):
        start = BusinessDate.diff_in_years(self.origin, s)
        end = BusinessDate.diff_in_years(self.origin, e)

        func = (lambda u:
                self.foreign_curve.volatility(u) ** 2 +
                self.volatility(u) ** 2 +
                self.domestic_curve.volatility(u) ** 2 -
                self.rate_correlation * self.domestic_curve.volatility(u) * self.foreign_curve.volatility(u) +
                self.foreign_correlation * self.volatility(u) * self.foreign_curve.volatility(u) -
                self.domestic_correlation * self.volatility(u) * self.domestic_curve.volatility(u))
        part, err = integrate.quad(func, start, end)
        return -0.5 * part

    def _calc_diffusion_integrals(self, s, e):
        start = BusinessDate.diff_in_years(self.origin, s)
        end = BusinessDate.diff_in_years(self.origin, e)

        func = (lambda u: -self.domestic_curve.calc_integral_B(u, end) * self.domestic_curve.volatility(u))
        part_d, err = integrate.quad(func, start, end)

        func = (lambda u: -self.foreign_curve.calc_integral_B(u, end) * self.foreign_curve.volatility(u))
        part_f, err = integrate.quad(func, start, end)

        part_x, err = integrate.quad(self.volatility, start, end)
        return part_d, part_x, part_f

    # pre calculate integrals

    def pre_calculate(self, s, e):
        self._pre_calc_drift[s, e] = self._calc_drift_integrals(s, e)
        self._pre_calc_diffusion[s, e] = self._calc_diffusion_integrals(s, e)

    # evolve process

    def evolve(self, x, s, e, q):
        r"""
        :param float x: current state value, i.e. value before evolution step
        :param BusinessDate s: current point in time, i.e. start point of next evolution step
        :param BusinessDate e: next point in time, i.e. end point of evolution step
        :param [float, float, float] q: standard normal random list number to do step
        :return float: next state value, i.e. value after evolution step

        evolves process state `x` from `s` to `e` in time depending of standard normal random variable `q`
        """
        # todo handle if not isinstance(self.inner_factor, RiskFactorModel), i.e. len(q)==2

        if (s, e) not in self._pre_calc_drift:
            d = self._calc_drift_integrals(s, e)
        else:
            d = self._pre_calc_drift[s, e]

        if (s, e) in self._pre_calc_diffusion:
            v_d, v_x, v_f = self._pre_calc_diffusion[s, e]
        else:
            v_d, v_x, v_f = self._calc_diffusion_integrals(s, e)

        return x * exp(d - v_d * q[0] + v_x * q[1] + v_f * q[2])


class HullWhiteFxRate(HullWhiteFxRateFactorModel):

    def __init__(self, value=1.0, origin=None, day_count=None,
                 domestic_curve=None, foreign_curve=None, volatility=0.0,
                 domestic_correlation=0., foreign_correlation=0., rate_correlation=0., correlation=None):
        origin = BusinessDate() if origin is None else origin
        inner_factor = FxRate(value, origin, day_count)
        domestic_curve = HullWhiteCurve([inner_factor.origin], [0.]) if domestic_curve is None else domestic_curve
        foreign_curve = domestic_curve if foreign_curve is None else foreign_curve
        super(HullWhiteFxRate, self).__init__(inner_factor, domestic_curve, foreign_curve, volatility,
                                              domestic_correlation, foreign_correlation, rate_correlation,
                                              correlation)


class HullWhiteMultiCurrencyCurveFactorModel(HullWhiteCurveFactorModel):
    """
        build HullWhiteMultiCurrencyCurve from HullWhiteCurves and HullWhiteFxCurve.
        Terminal measure date in foreign_curve is ignored since it is taken from domestic_curve.
        initializes foreign Hull White drift in multi currency model
    """

    def __init__(self, inner_factor, domestic_hw_curve, hw_fx_curve):
        """

        :param HullWhiteCurveFactorModel inner_factor:
        :param HullWhiteCurveFactorModel domestic_hw_curve:
        :param HullWhiteFxRateFactorModel hw_fx_curve:

        """
        if not isinstance(inner_factor, HullWhiteCurveFactorModel):
            names = self.__class__.__name__, HullWhiteCurveFactorModel.__name__, inner_factor.__class__.__name__
            raise TypeError('%s requires inner_factor of type %s. %s given.' % names)

        if not isinstance(domestic_hw_curve, HullWhiteCurveFactorModel):
            names = self.__class__.__name__, HullWhiteCurveFactorModel.__name__, domestic_hw_curve.__class__.__name__
            raise TypeError('%s requires curve argument of type %s. %s given.' % names)

        if not isinstance(hw_fx_curve, HullWhiteFxRateFactorModel):
            names = self.__class__.__name__, HullWhiteFxRateFactorModel.__name__, hw_fx_curve.__class__.__name__
            raise TypeError('%s requires fx argument of type %s. %s given.' % names)

        super(HullWhiteMultiCurrencyCurveFactorModel, self).__init__(inner_factor,
                                                                     inner_factor.mean_reversion,
                                                                     inner_factor.volatility,
                                                                     domestic_hw_curve.terminal_date)

        # collect parameter for multi currency Hull White model
        self._domestic_model = domestic_hw_curve
        self._fx_model = hw_fx_curve

    def calc_integral_I2(self, s, t):
        r"""
        calculates the following integral (see formula for the step in the MC evolution)

        .. math:: \textrm{Var}(\chi(t) | \mathcal{F}_s) = \int_s^t \sigma^2_d(u)B^2_d(u, T) +
         \sigma^2_f(u)B^2_f(u,T) + \sigma^2_{FX}(u) \\
         + 2\left(- \rho_{d,f} B_f(u, T)\sigma_f(u)B_d(u, T)\sigma_d(u)
         + \left( - \rho_{f,FX} B_f(u, T)\sigma_f(u)
         + \rho_{d,FX} B_d(u, T)\sigma_d(u) \right) \sigma_{FX}(u) \right)\,\mathrm{d}u

        :param float s:
        :param float t:
        :return float:
        """
        if not self._fx_model.foreign_correlation and not self._fx_model.rate_correlation:
            return super(HullWhiteMultiCurrencyCurveFactorModel, self).calc_integral_I2(s, t)

        terminal_date_yf = BusinessDate.diff_in_years(self.origin, self.terminal_date)

        # todo could use static version self. calc_integral_B(u, terminal_date_yf, domestic_mean_reversion)
        func1 = (lambda u: self.calc_integral_I1(u, t)
                           * (self.volatility(u) ** 2 * self.calc_integral_B(u, t) -
                              self._fx_model.rate_correlation *
                              self.volatility(u) *
                              self._domestic_model.volatility(u) *
                              self._domestic_model.calc_integral_B(u, terminal_date_yf) -
                              self._fx_model.foreign_correlation * self.volatility(t) * self._fx_model.volatility(t)))
        part1, err1 = integrate.quad(func1, s, t)

        part2 = self.calc_integral_B(s, t) * \
                self.calc_integral_I1(s, t) * \
                self.calc_integral_volatility_squared_with_I1_squared(0., s)

        return part1 + part2


class HullWhiteMultiCurrencyCurve(HullWhiteMultiCurrencyCurveFactorModel):
    """
        initializes foreign Hull White drift in multi currency model
    """

    def __init__(self, domain=(), data=(), interpolation=None,
                 origin=None, day_count=None, forward_tenor=None,
                 mean_reversion=0.0001, volatility=0.0,
                 domestic_hw_curve=None, hw_fx_curve=None):
        """

        :param list(BusinesDate) domain:
        :param list(float) data:
        :param (dcf.interpolation, dcf.interpolation, dcf.interpolation) interpolation:
        :param BusinessDate origin:
        :param function day_count:
        :param BusinessPeriod forward_tenor:
        :param float mean_reversion:
        :param TimeDependentParameter or float volatility:
        :param HullWhiteCurveFactorModel domestic_hw_curve:
        :param HullWhiteFxRateFactorModel hw_fx_curve:
        :param float foreign_correlation:
        :param float rate_correlation:

        """
        terminal_date = domain[-1] if domain else None
        terminal_date = terminal_date if domestic_hw_curve is None else domestic_hw_curve.terminal_date
        domestic_hw_curve = HullWhiteCurve() if domestic_hw_curve is None else domestic_hw_curve
        hw_fx_curve = HullWhiteFxRate() if hw_fx_curve is None else hw_fx_curve
        inner_factor = ZeroRateCurve(domain, data, interpolation, origin, day_count, forward_tenor)
        inner_factor = HullWhiteCurveFactorModel(inner_factor, mean_reversion, volatility, terminal_date)

        super(HullWhiteMultiCurrencyCurve, self).__init__(inner_factor=inner_factor,
                                                          domestic_hw_curve=domestic_hw_curve,
                                                          hw_fx_curve=hw_fx_curve)


