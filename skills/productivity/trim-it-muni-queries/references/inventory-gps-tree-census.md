# GPS Tree Inventory Queries (InventoryDetail)

The per-tree citywide GPS census lives in `gsts.dbo.InventoryDetail` — 274 columns,
~1.79M rows company-wide. Each municipal project (identified by `ProjectID`) houses
all of that city's tree records. This is the data set Brent refers to when he says
"inventory data" — lat/long, species, DBH, zone/district/area, pruning cycle, condition,
maintenance scheduling.

## Where the tree records live (and don't)

- ✅ **`InventoryDetail`** — the actual per-tree census. Query by `ProjectID`.
- ❌ **`Inventories`** — a header/summary table (13 columns: InventoryID, GSTSID,
  CustomerRef, Latitude, Longitude, ProjectID, Desc1, AreaID, StatusID, …). It is
  typically **empty** for a project even when `InventoryDetail` has thousands of rows.
  Do not waste time here.
- **`ProjectInventory`** — a higher-level inventory-summary roll-up (prior/current/future
  year qty & totals). One row per project; useful for cycle-level aggregate view, not
  per-tree detail.

## Key columns (verified 2026-07-15, City of Industry — 9,685 trees)

### Location / GIS
| Column | Notes |
|--------|-------|
| `Latitude` / `Longitude` | GPS coordinates |
| `OrigLatitude` / `OrigLongitude` | Original capture coords (pre-move) |
| `Northing` / `Easting` | State plane coords |
| `StreetNumber`, `StreetName`, `StreetNameID`, `StreetNumberInt` | Address |
| `TreeLocation`, `LocationSide`, `LocationSeq` | Site placement |
| `ZoneDefID` / `ZoneDefRef` | Zone |
| `DistrictRef`, `DistrictID` | District |
| `AreaRef` | Area |
| `GeoCity`, `GeoZipCode`, `GeoState`, `LocationZipRegionID` | Geo-located city/zip |

### Tree attributes
| Column | Notes |
|--------|-------|
| `SpeciesRef` | Species (reference code) |
| `DBH`, `DBHRange` | Diameter at breast height |
| `Height`, `HeightRange` | Height + banded range |
| `Crown` | Crown spread |
| `SizeCode`, `OriginalSizeCode`, `OrigSizeCode` | Size classification |
| `Stems` | Multi-stem notation |
| `ConditionDefID` | Condition rating (FK) |
| `StructureRatingID` | Structure rating (FK) |
| `MaintNeedID` | Maintenance need (FK) |
| `OverheadUtil` (bit) | Overhead utilities present |
| `GrowSpaceID`, `SpaceSize`, `ParkwayType`, `ParkwaySize` | Site/grow-space |

### Pruning cycle / maintenance scheduling
| Column | Notes |
|--------|-------|
| **`PruningFrequency`** | **The pruning-cycle year assignment** (e.g. 2024, 2022). This is what Brent means by "pruning cycle '2024'". Integer year, NOT a string. |
| `ServiceTypeID`, `ServiceTypeDesc1` | Service type |
| `EstTrimTime`, `EstCleanTime`, `EstCycleTime`, `EstTPH` | Time/cost estimates |
| `IsRecentTrim`, `RecentTrimBy` | Recently-trimmed flag |
| `CurrentYearFlag` | Single-char status: `.` = none, `R` = recommended, `A` = approved |
| `Prior01`–`Prior05` / `CurrentComplete` / `CurrentScheduled` / `Future01`–`Future06` | Multi-year cycle dates |
| `SeasonID`, `CurrentYearSeasonID` | Season assignment |

### Lifecycle / monitoring
| Column | Notes |
|--------|-------|
| `IsMonitor` (bit) | Monitor tree |
| `IsPlantedByOthers` / `IsPlantedByGSTS`, `PlantingDate` | Planting origin |
| `IsIrrigation`, `IsToBeWatered`, `WateringStoppedDate` | Irrigation tracking |
| `ConfirmationDate`, `IsNewObservation`, `IsNewConfirmation` | Field confirmation |
| `ReplacementClassID`, `ReplacementCost` | Replacement data |
| `IsDeleted`, `DeletedDate`, `IsMoved`, `MovedFromLatitude/Longitude` | Lifecycle changes |

## Verified query patterns

### Count trees by pruning cycle for a city
```sql
SELECT PruningFrequency, COUNT(*) AS TreeCount
FROM gsts.dbo.InventoryDetail
WHERE ProjectID = <pid>
GROUP BY PruningFrequency
ORDER BY TreeCount DESC;
```
City of Industry (ProjectID 1095104) returned cycles spanning 2019–2025:
2024 (3,776) | 2022 (2,530) | 2023 (1,227) | 2025 (1,172) | 2019 (425) | 2021 (288) | 2020 (252) | NULL (15).

### Total tree count for a city
```sql
SELECT COUNT(*) AS TreeCount
FROM gsts.dbo.InventoryDetail
WHERE ProjectID = <pid>;
```

### Pruning-cycle status flag distribution
```sql
SELECT CurrentYearFlag, COUNT(*) AS cnt
FROM gsts.dbo.InventoryDetail
WHERE ProjectID = <pid>
GROUP BY CurrentYearFlag;
-- '.' = not scheduled, 'R' = recommended, 'A' = approved
```

## Schedule of Compensation (LocationServiceTypes)

The **Schedule of Compensation** — the per-service, per-size rate card — lives in
`gsts.dbo.LocationServiceTypes`. Brent referred to it as being linked from the
"Location tab" in TRIM IT. It is reached via the project's **LocationID**, not
directly from `ProjectID`.

### Discovery path (verified 2026-07-15, City of Industry)

1. **Find the project's LocationID:**
   ```sql
   SELECT LocationID, Desc1 FROM gsts.dbo.Locations WHERE ProjectID = <pid>;
   -- City of Industry → LocationID 1273739
   ```

2. **Pull the full rate card:**
   ```sql
   SELECT LocationServiceTypeID, Desc1, SeqOrder, ServiceTypeID,
          SizeCode, BasePrice, BudgetedQty, BudgetedTotalPrice,
          DistrictID, ZoneDefID, ItemCode
   FROM gsts.dbo.LocationServiceTypes
   WHERE LocationID = <locid>
   ORDER BY SeqOrder, SizeCode;
   ```

### What the rate card contains

Three service categories, each with per-size or per-species rates:

| Service Category | ServiceTypeID | Structure |
|-----------------|--------------|-----------|
| Tree Pruning | 149 | By DBH size class (0-6", 7-12", 13-18", 19-24", 25-30", 31+") |
| Palm Trimming | 149 | By species (Cal Fan, Canary Is., Date, King, Med, Mex Fan, Queen, Windmill) |
| Tree Removal + Stump Grinding | 47 | By DBH size class (same bands as pruning) |
| Tree Planting | 21 | By container size (15-gal, 24" box, 36" box, 48" box) |

### Key columns
| Column | Notes |
|--------|-------|
| `Desc1` | Full description: "Service Request Tree Pruning: 0-6\" DBH" |
| `SizeCode` | Size band: "0-6", "07-12", "13-18", "19-24", "25-30", "31+", or NULL for palms |
| `BasePrice` | The per-tree rate (e.g. $89, $149, $559) |
| `SeqOrder` | Display order on the schedule |
| `ServiceTypeID` | Service type (149 = pruning, 47 = removal, 21 = planting) |
| `ZoneDefID` | Zone scoping (all line items shared the same zone in Industry) |
| `DistrictID` | NULL on all Industry rows — rate card is city-wide, not per-district |

### Verification note

The `BasePrice` values on `LocationServiceTypes` align with the most common
`InventoryDetail.BasePrice` values per size class, confirming this is the canonical
rate source. Individual tree `BasePrice` values vary slightly (some trees have
$0 or different rates due to service-request overrides), but the Schedule of
Compensation holds the contract-defined rates.

## Scope boundary — municipal inventory only

Irvine Company retail, HOA, and commercial properties also have `InventoryDetail`
data in TRIM IT (the table is company-wide, 1.79M rows). Muni Bot works **Track 1
(municipal) only**. If Brent sends a request involving non-municipal properties
(e.g., Irvine Company retail proposals with species questions), **flag the scope
boundary and confirm with Brent/Jason before proceeding.** Do not silently cross
into commercial work — even if the data is technically accessible via the same
tables. (Verified 2026-07-15: Brent emailed Irvine Company retail proposal IDs;
Muni Bot correctly flagged the scope boundary before proceeding.)

## Pitfalls

1. **`CurrentYear` is NULL — don't use it for cycle assignment.** Despite the name,
   `CurrentYear` was entirely NULL for City of Industry. The pruning cycle lives in
   **`PruningFrequency`**. Confirmed empirically 2026-07-15.
2. **`Inventories` table is a red herring.** It looks like it should hold tree records
   but is empty for projects with active `InventoryDetail` rows. Skip it.
3. **274 columns — don't `SELECT *` in production queries.** Pull only the columns you
   need; the full row is wide and slow. Use `SELECT TOP 1 *` only for schema discovery.
4. **Always scope by `ProjectID`.** Without it you hit all 1.79M rows company-wide.
5. **`PruningFrequency` is an integer year, not a cycle label or interval.** A value of
   `2024` means "this tree is on the 2024 pruning cycle," not "prune every 2024 years."
6. **`DistrictRef` text label is unreliable — use `DistrictID`.** For City of Industry,
   `DistrictRef` was only populated on ~1,047 of 3,985 East-district trees (label "EAST").
   The remaining ~2,938 rows had blank or NULL `DistrictRef` but still belonged to
   `DistrictID = 18781`. **Always filter/join on `DistrictID` (the integer FK), then
   show `DistrictRef` as a display label if present.** Never filter by `DistrictRef`
   text alone — you'll silently drop 70%+ of the district.
7. **Schedule of Compensation is NOT in `PricingSizes`, `PricingGroupRates`, or
   `InventoryPricingHistory`.** Those tables exist but were empty for this project. The
   rate card lives in `LocationServiceTypes`, linked via `Locations.ProjectID` →
   `LocationID`. See the Schedule of Compensation section above.
