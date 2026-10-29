# Global Superstore — Excel Budget vs Actual Dashboard: Data Notes

## Files in this folder
| File | What it is | Use |
|---|---|---|
| `Global_Superstore2.csv` / `.xlsx` | Raw actuals from Kaggle (apoorvaappz/global-super-store-dataset) | Fact table source — import via Power Query, never edit by hand |
| `Budget_2014_wide.csv` | 2014 budget, months as columns (54 rows) | The "what finance sends you" format — **unpivot this in Power Query** |
| `Budget_2014_long.csv` | Same budget, one row per month (635 rows), includes Budget Profit | Answer key / sanity check for your unpivot |
| `archive.zip` | Original Kaggle download | Can delete |

## Actuals: profile
- **51,290 rows × 24 columns**, one row per order line. No duplicate rows, `Row ID` is unique.
- **Order Date range: 1 Jan 2011 – 31 Dec 2014.** Format is `dd-mm-yyyy` — set locale to English (UK) or use `Date.FromText` with day-first in Power Query, otherwise Excel will silently swap day/month for dates ≤ 12.
- Only null column: `Postal Code` (41,296 blanks — non-US rows). Keep it as text, not number.
- Yearly sales: 2011 $2.26M → 2012 $2.68M → 2013 $3.41M → 2014 $4.30M (+26% YoY in 2014).

### Dimensions
| Field | Cardinality | Values |
|---|---|---|
| Market | 7 | US, APAC, EU, Africa, EMEA, LATAM, Canada |
| Region | 13 | East, West, Central, South, North, Oceania, Central Asia, North Asia, Southeast Asia, Africa, EMEA, Caribbean, Canada |
| Category | 3 | Technology, Furniture, Office Supplies |
| Sub-Category | 17 | Phones, Chairs, Copiers, Tables, Binders, Storage, … |
| Segment | 3 | Consumer, Corporate, Home Office |
| Ship Mode | 4 | Same Day, First Class, Second Class, Standard Class |
| Order Priority | 4 | Critical, High, Medium, Low |
| Country / City | 147 / 3,636 | |
| Customers | 1,590 | |
| Products | 10,292 Product IDs | see quirk 1 |
| Orders | 25,035 Order IDs | see quirk 2 |

### Measures
| Field | Mean | Min | Max | Note |
|---|---|---|---|---|
| Sales | 246.5 | 0.44 | 22,638 | Net of discount already |
| Quantity | 3.5 | 1 | 14 | |
| Discount | 0.14 | 0 | 0.85 | Fraction, not % |
| Profit | 28.6 | −6,600 | 8,400 | 25% of lines have Profit ≤ 0 |
| Shipping Cost | 26.4 | 0 | 934 | |

## Three data quirks (deliberately leave these in — fixing them is the "data cleaning" bullet)
1. **457 Product IDs map to more than one Product Name.** A Products dimension keyed on Product ID alone will fail the uniqueness check in Power Pivot. Fix: build a surrogate key = `Product ID & "|" & Product Name` in Power Query, or key the dimension on Product Name. Document which you chose.
2. **659 Order IDs are shared by more than one customer** (same Order ID in different markets). Treat `Order ID + Customer ID` as the order grain, or just leave the fact table at line level and don't build an Orders dimension.
3. **Ship Date ≥ Order Date always holds** (0 violations) — good; you can safely compute `Ship Days = Ship Date − Order Date` as a calculated column.

## Budget table: how it was built (say this in your README, it's a strength not a weakness)
- Grain: Market × Region × Category × Month, for **2014 only**.
- Formula: `2013 actual sales × 1.25 × N(1, 0.07)` with a fixed random seed; Budget Profit = `2013 profit × 1.28 × N(1, 0.09)`.
- Result: 2014 budget totals **$4,300,517** vs 2014 actual **$4,299,866** — company is on plan overall, but region × category cells range from **−33% (Canada / Office Supplies)** to **+70% (Canada / Furniture)**. That spread is the dashboard's story.
- Region × Category variance preview (Actual vs Budget, 2014):

| Region | Furniture | Office Supplies | Technology |
|---|---|---|---|
| West | −23.9% | +43.5% | +13.7% |
| North Asia | −30.1% | +2.5% | +0.7% |
| Caribbean | −12.3% | −14.3% | −14.7% |
| Canada | +70.2% | −32.7% | −4.3% |
| Central Asia | +12.3% | +57.0% | −20.7% |
| EMEA | +45.3% | −5.4% | +16.2% |
| East | +3.9% | −16.2% | −3.8% |
| Central | −2.5% | +0.2% | −5.0% |

## Suggested Power Query steps
1. `Actuals` ← CSV, set types, `Order Date`/`Ship Date` as Date (day-first), `Postal Code` as Text, add `Year`, `Month`, `Quarter`, `Ship Days`, `Discount Band` (0 / 0–20% / 20–50% / 50%+), `Product Key`.
2. `Budget` ← `Budget_2014_wide.csv`, **Unpivot Other Columns** on the month columns → rename to `Month Name`, `Budget Sales`; add `Month` number via a lookup; set types.
3. `Dim_Date` ← generate 2011-01-01 … 2014-12-31 (`List.Dates`), with Year/Quarter/Month/MonthName columns. Mark as date table in Power Pivot.
4. `Dim_Product`, `Dim_Customer`, `Dim_Geo` ← Reference `Actuals`, keep key + attributes, Remove Duplicates.
5. Load all to the Data Model only (not to sheets), except a `Dim_Date` sheet if you want slicers on it.

## Starter DAX measures
```
Revenue        := SUM ( Actuals[Sales] )
Gross Profit   := SUM ( Actuals[Profit] )
Margin %       := DIVIDE ( [Gross Profit], [Revenue] )
Budget Sales   := SUM ( Budget[Budget Sales] )
Variance       := [Revenue] - [Budget Sales]
Variance %     := DIVIDE ( [Variance], [Budget Sales] )
Revenue PY     := CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
YoY Growth %   := DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )
Orders         := DISTINCTCOUNT ( Actuals[Order ID] )
AOV            := DIVIDE ( [Revenue], [Orders] )
Avg Ship Days  := AVERAGE ( Actuals[Ship Days] )
```
Note: Budget joins to the model on Region + Category + Month, not on a single key. Either build a composite key column (`Region & Category & Year & Month`) on both tables in Power Query, or relate Budget to Dim_Date / Dim_Geo / a small Dim_Category table separately.
