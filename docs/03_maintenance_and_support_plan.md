# Maintenance and Support Plan
## Nepal Car Rental System (NCRS)

**Programme:** Master of Software Engineering - 180 Credits
**Course:** Professional Software Engineering (MSE-800) (Level 8, 15 Credits, Version 1)
**Assessment:** Assessment 1 - Object-Oriented Programming Assignment - Task 3: Software Evolution
**Lecturer:** Mohammad Norouzifard
**Student Name:** Anish Shrestha
**Student ID:** 270889991
**Institution:** Yoobee College, New Zealand

---

## 1. Purpose of This Document

This document is Task 3 of Assessment 1 ("Software Evolution", weighted 30%). It
outlines how the Nepal Car Rental System (NCRS) would be maintained, versioned,
and evolved safely over time if development continued beyond this assignment -
covering the three strategies the rubric specifically asks for: **managing
software maintenance**, **versioning**, and **backward compatibility** - plus how
updates, bug fixes, and new features would be handled, and why these practices
matter for the system's long-term success.

---

## 2. Managing Software Maintenance

### 2.1 The four types of maintenance this plan covers

| Type | What it means for NCRS | Example |
|---|---|---|
| **Corrective** | Fixing a bug reported after release | A booking's conflict check misses an edge case on the exact return date |
| **Adaptive** | Adjusting the system to a changed environment | A newer Python version changes how `sqlite3` handles a data type |
| **Perfective** | Improving something that already works | Making the CLI tables paginate instead of dumping 200 rows at once |
| **Preventive** | Reducing future risk before it becomes a bug | Adding a test for a code path nobody has broken yet, but could |

### 2.2 Why the project's own architecture makes maintenance manageable

This is not an abstract policy - it follows directly from decisions already made
in the codebase:

- **Layered architecture** (`cli/` -> `services/` -> `models/` -> `database/`,
  see `docs/01_requirements_analysis.md` section 18). A bug fix to *how* a
  booking's cost is calculated only ever needs a change in
  `models/booking.py`'s `calculate_cost()` - never in the CLI screens that
  display it. This containment is what makes maintenance safe rather than
  risky: fixing one thing cannot silently break an unrelated screen.
- **One shared validation layer** (`utils/validators.py`). If a validation
  rule needs to change (e.g. accepting international phone numbers), it
  changes in exactly one function, and every screen that uses it is fixed at
  once - instead of hunting through a dozen copy-pasted checks.
- **An automated regression test suite** (`tests/`, run with `pytest`). Before
  any fix or new feature is considered "done", the full suite is re-run. A
  failing test that used to pass is the earliest possible warning that a
  change broke something else - far cheaper to catch here than after a real
  user finds it.
- **Heavy inline documentation**. Every file explains not just *what* it does
  but *why* it was built that way (see, for example, the Singleton
  explanation in `database/db_connection.py`). This matters because most of
  the lifetime cost of maintaining software is spent understanding code
  someone else (or "past you") wrote - not writing new code.

### 2.3 A concrete maintenance workflow

1. A bug or change request is reported (in a real deployment: a support
   ticket or GitHub Issue; for this assignment: feedback from the lecturer/marker).
2. It is reproduced locally, and a **failing automated test is written first**
   wherever practical - this both proves the bug is understood and stops it
   from silently reappearing later ("regression").
3. The fix is made in the *one* layer responsible for that behaviour.
4. The full `pytest` suite is re-run - it must be all green before the fix is
   considered complete.
5. The change is committed to Git with a clear, descriptive message, and
   `docs/01_requirements_analysis.md` / this document are updated if the fix
   changes any documented behaviour.

---

## 3. Versioning

### 3.1 Scheme: Semantic Versioning (SemVer)

NCRS already exposes its version as `config.PROJECT_VERSION` (currently
`"1.0.0"`, shown on the CLI's About screen - see `cli/about_screen.py`). Going
forward, this project would follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`):

- **MAJOR** (`1.x.x` -> `2.0.0`): a change that breaks backward compatibility -
  for example, changing the `bookings` table's columns in a way old data
  cannot be automatically migrated into, or changing the pricing formula
  itself (BR3/BR3a) rather than just its rate.
- **MINOR** (`1.0.x` -> `1.1.0`): a new feature added in a backward-compatible
  way - for example, adding a "vehicle photo" field that is optional, so
  existing data and existing screens keep working unchanged.
- **PATCH** (`1.0.0` -> `1.0.1`): a bug fix with no feature change and no
  compatibility impact - for example, fixing the phone number validation
  regex.

### 3.2 Where version information lives, and how it is tracked

- `config.PROJECT_VERSION` is the single source of truth for the running
  version, shown on the About screen - exactly like `STUDENT_NAME` and the
  other identity constants in `config.py`, it lives in ONE place so it never
  goes out of sync across files.
- Git tags (e.g. `v1.0.0`, `v1.1.0`) would mark exactly which commit each
  released version corresponds to, so any past version can be checked out and
  run again if needed - essential for debugging "this used to work" reports.
- A `CHANGELOG.md` would record, for every version bump, what changed and
  why - in practice this is often more valuable to a maintainer than the diff
  itself, because it explains *intent*, not just *what lines changed*.

### 3.3 Database schema versioning

`database/schema.py` currently uses `CREATE TABLE IF NOT EXISTS`, which is
perfect for a first release (see the file's own comments) but is not, by
itself, enough once real user data exists across versions. The plan for
evolving the schema safely is:

1. Add a `schema_version` row to the `settings` table (the same table already
   used for `rate_per_km` - see `database/schema.py`), starting at `1`.
2. Any future schema change ships as a small, numbered **migration script**
   (e.g. `database/migrations/002_add_vehicle_photo.py`) that: checks the
   current `schema_version`, applies only the SQL needed to move forward one
   step (using `ALTER TABLE` where SQLite supports it), and then updates
   `schema_version` to `2`.
3. `RentalSystem.__init__()` (see `services/rental_system.py`) would run any
   pending migrations automatically on startup - exactly the same principle
   already used for `init_database()` and `seed_if_empty()`: the program
   always leaves the database in a known, current state without the user
   needing to run any separate command.

---

## 4. Backward Compatibility

### 4.1 Data compatibility

Because SQLite stores the whole database as one file
(`ncrs_database.sqlite3`), backward compatibility means: **a newer version of
NCRS must still be able to open a database file created by an older version,
without losing or corrupting existing bookings, users, or payments.** The
migration approach in section 3.3 exists specifically for this reason - it
only ever *adds to* the schema (new tables, new nullable columns), never
silently drops or renames something an older version relied on.

### 4.2 API/interface compatibility (the service layer)

Every CLI screen calls into `services/*.py` functions by name and by
parameter order (see, for example, `booking_service.create_booking(...)`).
Two rules keep this stable across versions:

- **Add new parameters as optional, with a default value**, rather than
  inserting a new required parameter in the middle of an existing function's
  signature. `booking_service.create_booking(..., driver_id: int = None)` is
  already written this way - a caller that does not know about drivers yet
  still works.
- **Never change what a function returns without a version bump.** If
  `list_all_bookings()` needs to start returning extra information, that is a
  MINOR change (add a new attribute to the `Booking` object) rather than
  restructuring the return type itself, which would be a MAJOR, breaking
  change.

### 4.3 Configuration compatibility

`config.py` centralises every constant the system depends on (registration
keywords, currency symbol, default rate per km). If a keyword or default ever
needs to change, the OLD value should keep working for a documented
deprecation window (for example, one MINOR version) with a warning, rather
than being removed outright in the very next release - giving anyone relying
on the old keyword time to adjust.

---

## 5. Handling Updates, Bug Fixes, and New Feature Additions

| Change type | Process |
|---|---|
| **Bug fix** | Reproduce -> write a failing test -> fix the ONE responsible layer -> re-run the full `pytest` suite -> release as a PATCH version |
| **New, backward-compatible feature** | Design it so existing data/behaviour is untouched (e.g. a new optional field, a new menu option) -> implement with the same layered structure and comment style as the rest of the codebase -> add new tests covering it -> release as a MINOR version |
| **Breaking change** | Only when unavoidable (e.g. the pricing formula itself must change) -> write a database migration (section 3.3) -> update ALL documentation (`docs/01_requirements_analysis.md`, `README.md`, this file) -> release as a MAJOR version with a clear changelog entry explaining what breaks and why |

A Git branching approach supporting this: `main` always reflects the latest
released version; a short-lived `feature/<name>` or `fix/<name>` branch is
created for each change, tested locally (`pytest`), then merged back into
`main` via a pull request - giving every change a reviewable, revertible
history, and keeping `main` always in a state that could be zipped up and
submitted/deployed.

---

## 6. Why This Matters for Long-Term Success

A car rental system that only ever works "as originally submitted" has no
real value once vehicles are added, rates change, or a new business rule
appears - which is exactly what happens to real software once it leaves an
assignment folder. The practices in this plan exist to keep three things true
as NCRS grows:

- **Correctness does not silently regress.** The automated test suite is what
  actually enforces this - not good intentions.
- **Change is contained, not chaotic.** The layered architecture and the
  service-layer compatibility rules mean one change does not ripple
  unpredictably through the whole system.
- **The system's history is understandable.** Semantic versioning, a
  changelog, and small, well-described commits mean anyone (including the
  original author returning after months away) can answer "what changed, and
  why?" quickly - which is, in the end, most of what professional software
  engineering practice is actually for.
