
-----------------
API Documentation
-----------------

.. toctree::


Risk Factor Modeling
====================

.. currentmodule:: shortrate

.. autosummary::
    :nosignatures:

    risk_factor_model.RiskFactor
    risk_factor_model.RiskFactorModel
    risk_factor_model.RiskFactorState
    risk_factor_model.RiskFactorProducer
    risk_factor_model.MultiRiskFactorProducer
    risk_factor_model.RiskFactorConsumer

.. inheritance-diagram:: risk_factor_model

.. automodule:: risk_factor_model


Market Risk Factors
===================


.. autosummary::
    :nosignatures:

    shortrate.market_risk_factor.BrownianZeroRateCurve
    shortrate.market_risk_factor.GBMFxCurve

.. inheritance-diagram:: market_risk_factor

.. automodule:: market_risk_factor


The Hull White Model
====================

.. py:currentmodule:: shortrate.hullwhite_model

.. autosummary::
    :nosignatures:

    hullwhite_model.HullWhiteCurve

.. inheritance-diagram:: hullwhite_model

.. automodule:: hullwhite_model


Multi Currency Hull White Model Extension
=========================================

.. py:currentmodule:: shortrate.hullwhite_multicurrency_model

.. autosummary::
    :nosignatures:

    hullwhite_multicurrency_model.HullWhiteFxCurve
    hullwhite_multicurrency_model.HullWhiteMultiCurrencyCurve

.. inheritance-diagram:: hullwhite_multicurrency_model

.. automodule:: hullwhite_multicurrency_model
