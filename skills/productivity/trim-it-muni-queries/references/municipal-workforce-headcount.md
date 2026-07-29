# Municipal Field-Staffing Average

Use this when asked how many field workers, on average, are working municipal jobs over a historical period.

## Metric to report

When named employee-to-job assignments do not reconcile to actual attendance, report an **hours-supported equivalent daily headcount**, not a literal distinct-person count:

```text
Equivalent municipal workers/day
  = municipal completed crew-hours
    / actual average hours per worker-day
    / active workdays
```

Where:

- Municipal = the work order's project has `ProjectGroupDefID = 11`.
- Municipal completed crew-hours = `CrewSheets.CompletedHours` by `CrewSheets.WorkDate`, with `CrewSheets.StatusDefID IN (5,39)`; use `ActHours` only as a verified fallback.
- Actual worker-days and payroll hours = `CrewMemberCalendars` joined to `Calendars`, requiring `TotalHours > 0` and `ISNULL(SickHours,0)=0`.
- Default executive view = Monday-Friday active days; state the date window and whether weekends are excluded.

## Why this method

`CrewMemberCalendars` is authoritative for who actually worked and how many hours were recorded. `CrewAssignments` can be sparse or incomplete for historical market attribution. Before using assignment-based distinct headcount, validate its coverage against `CrewMemberCalendars`:

- average total positive-hour workers/day;
- average workers with positive assignment hours/day;
- assignment hours versus payroll hours.

If assignment coverage is materially incomplete, do not present the assignment count as actual staffing. Use equivalent headcount and label it clearly.

## Query outline

1. Build `MuniProjects` from `ProjectGroups` where `ProjectGroupDefID = 11`.
2. Build active daily worker totals from `Calendars` + `CrewMemberCalendars`.
3. Sum municipal `CrewSheets.CompletedHours` by `WorkDate` through `WorkOrders.ProjectID`.
4. Left join municipal hours onto all active workdays so zero-municipal days remain in the denominator.
5. Compute the weighted actual hours per worker-day:

```sql
SUM(PayrollHours) / SUM(WorkerDays)
```

6. Compute equivalent daily municipal workers:

```sql
SUM(MuniCompletedHours)
/ (SUM(PayrollHours) / SUM(WorkerDays))
/ COUNT(ActiveWorkdays)
```

7. Return both YTD and monthly rows so the annual average has a trend check.

## Reporting controls

- Say **“approximately N equivalent field workers per weekday”**.
- Include completed municipal hours, active weekdays, actual hours per worker-day, and the through-date.
- Do not call an equivalent headcount a named-person count.
- Do not use future schedule-board declines as historical staffing evidence.
- PLAY may lag live; name the latest completed date represented in the calculation.