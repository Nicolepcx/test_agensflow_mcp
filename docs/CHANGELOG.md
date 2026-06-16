# Changelog

## [unreleased]

### Added
- `taskflow standup` command — prints a one-paragraph standup summary
  (totals, completion rate, overdue list).
- Recurrence engine (`core/recurrence.py`) — completing a recurring task
  spawns its next instance (daily/weekly/monthly/yearly).
- Plugin pipeline (`plugins/`) for list rendering: priority-sort and
  overdue-alert.

### Fixed
- (pending PR #1) `parse_due` crash on `feb 29` in non-leap years.

### Known issues
- #1 yearly-recurrence leap-day crash (parsing + recurrence).
- #2 concurrent writes lose updates / corrupt the store.

## [0.1.0] — 2026-05-15

Initial release.

- `taskflow add / list / done / rm` with JSON storage.
- Priority, due dates, tags, projects.
- Query filtering (done / priority / project / tag / overdue / text).
