CREATE OR ALTER VIEW dbo.v_monthly_demand AS
SELECT part_id, location_id, period, SUM(qty) AS demand_units
FROM dbo.demand_history
GROUP BY part_id, location_id, period;
GO

CREATE OR ALTER VIEW dbo.v_monthly_finance AS
SELECT period,
       SUM(qty * standard_price) AS standard_spend,
       SUM(qty * actual_price) AS actual_spend,
       SUM(qty * (actual_price - standard_price)) AS purchase_price_variance,
       SUM(budget) AS budget,
       SUM(qty * actual_price - budget) AS budget_variance,
       SUM(expedite_spend) AS expedite_spend
FROM dbo.purchase_orders
GROUP BY period;
GO
