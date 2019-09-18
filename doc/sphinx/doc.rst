
.. module:: shortrate

-----------------
API Documentation
-----------------

.. toctree::


Risk Factor Modeling
====================

.. py:currentmodule:: shortrate.risk_factor_model

.. autosummary::
    :nosignatures:

    RiskFactor
    RiskFactorModel
    RiskFactorState
    RiskFactorProducer
    MultiRiskFactorProducer
    RiskFactorConsumer

.. inheritance-diagram:: shortrate.risk_factor_model

.. automodule:: shortrate.risk_factor_model


Market Risk Factors
===================

.. py:currentmodule:: shortrate.market_risk_factor

.. autosummary::
    :nosignatures:

    GaussRiskFactorModel
    GeometricBrownianMotionRiskFactorModel
    GeometricBrownianMotionPriceFactorModel
    GeometricBrownianMotionPrice
    GeometricBrownianMotionFxRateFactorModel
    GeometricBrownianMotionFxRate
    GaussFlatSpreadZeroRateCurveFactorModel
    GaussFlatSpreadZeroRateCurve

.. inheritance-diagram:: shortrate.market_risk_factor

.. automodule:: shortrate.market_risk_factor


The Hull White Model
====================

Single Currency
---------------

.. py:currentmodule:: shortrate.hullwhite_model

.. autosummary::
    :nosignatures:

    HullWhiteCurveFactorModel
    shortrate.HullWhiteCurve

.. inheritance-diagram:: shortrate.hullwhite_model

.. automodule:: shortrate.hullwhite_model


Multi Currency Extension
------------------------

.. py:currentmodule:: shortrate.hullwhite_multicurrency_model

.. autosummary::
    :nosignatures:

    HullWhiteFxRateFactorModel
    HullWhiteFxRate
    HullWhiteMultiCurrencyCurveFactorModel
    HullWhiteMultiCurrencyCurve

.. inheritance-diagram:: shortrate.hullwhite_multicurrency_model

.. automodule:: shortrate.hullwhite_multicurrency_model
