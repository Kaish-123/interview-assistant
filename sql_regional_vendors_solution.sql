-- __define-ocg__ Regional Vendors: distribution by region for year 2018
SELECT
  varOcg.Region,
  varOcg.UniqueVendors,
  varOcg.TotalEntries
FROM (
  SELECT
    Region,
    COUNT(DISTINCT VendorID) AS UniqueVendors,
    COUNT(*) AS TotalEntries
  FROM maintable_70ZQ9
  WHERE Year = 2018
  GROUP BY Region
) AS varOcg
ORDER BY varOcg.UniqueVendors DESC, varOcg.TotalEntries DESC;
