# CHANGES - System Data Work

Date: 2026-02-05

Summary: Added frontend pages/routes and navigation for System Data (versions & periods), implemented period expand UI and wired version copy (existing). Logged all edits below so changes can be reverted if requested.

Modified/Added files:

- `frontend/src/components/LayoutProvider.tsx` - 2026-02-05
  - Added navigation item: **Sistem Verileri** -> `/system-data` (icon: Database)

- `frontend/src/App.tsx` - 2026-02-05
  - Imported `SystemDataPage`, `VersionsPage`, `PeriodsPage`.
  - Added protected routes:
    - `/system-data` -> `SystemDataPage`
    - `/system-data/versions` -> `VersionsPage`
    - `/system-data/periods` -> `PeriodsPage`
    - `/system-data/:entity` -> redirect helper `SystemDataRouteRedirect`

- `frontend/src/pages/PeriodsPage.tsx` (new) - 2026-02-05
  - New page to list periods, delete periods and expand periods using `systemDataApi.expandPeriods(start, end)`.
  - UI includes expand form (start/end inputs) and periods table.

Notes / Revert instructions:
- To revert these changes, remove the `Sistem Verileri` nav entry from `LayoutProvider.tsx`, remove the added routes and imports from `App.tsx`, and delete `frontend/src/pages/PeriodsPage.tsx` and this changelog file.

If you want, I can create a git patch or revert commit for you; tell me which revert method you prefer.
