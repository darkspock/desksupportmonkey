# E45: Asset Locations & Movement Tracking — Feature Slicing

## Features Summary

| # | Feature | Deps | Complexity | Status |
|---|---------|------|------------|--------|
| F0 | Location Foundation — entity, DB, CRUD, seeding | None | M | Done |
| F1 | Asset-Location Integration — move command, auto-location on assign/unassign/create/shipping, events | F0 | M | Done |
| F2 | Frontend — location mgmt page, asset detail/list UI, i18n | F1 | L | Done |
