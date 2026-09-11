# Nepal Car Rental System (NCRS)

**Programme:** Master of Software Engineering — 180 Credits
**Course:** Professional Software Engineering (MSE-800) — Level 8, 15 Credits, Version 1
**Assessment:** Assessment 1 — Object-Oriented Programming Assignment
**Lecturer:** Mohammad Norouzifard
**Student Name:** Anish Shrestha
**Student ID:** 270889991
**Institution:** Yoobee College, New Zealand

---

## 1. About This Project

Nepal Car Rental System (NCRS) is a Python application for managing a car
rental business: customer, vehicle-owner/driver, and administrator accounts; vehicle and
driver records; rental bookings with availability checking; automatic rental cost
calculation; a simulated payment record; and a Smart Waitlist + Auto-Notify feature for
vehicles that are already booked out.

It can be used two ways, side by side, against the exact same data:

- **The command-line interface (CLI)** — `main.py` — the original interface, with text
  menus and keyboard shortcuts. This is what sections 2-9 below describe.
- **A web interface** — `web/app.py` — an optional, later addition: the same system as
  simple HTML pages with buttons, links, and forms, opened in any web browser. See
  section 3 below.

Both share the exact same `services/`, `models/`, `database/`, and `utils/` code and the
exact same `ncrs_database.sqlite3` file — neither one is a copy of the other's logic, so
anything done from one is immediately visible from the other.

The system runs entirely offline using a local SQLite database file — no internet
connection, no external database server, and no paid third-party services of any kind
are required to install or run it (this applies to the web interface too — see section 3).

The system is themed around Nepal (vehicle registration plates, place names for
customer addresses) but uses New Zealand Dollars (NZD$) for all pricing, matching
the currency the student is billed and marked in.

## 2. How to Install and Run (Command-Line Interface)

1. Make sure Python 3.10+ is installed on your machine.
2. Open this folder in a terminal (or use VS Code's integrated terminal).
3. Install the third-party packages this project uses (see section 5):
   ```
   pip install -r requirements.txt
   ```
4. Run the program:
   ```
   python main.py
   ```
5. On first run, the program automatically creates its local SQLite database file and
   fills it with demo data (see section 4) — no manual setup needed.
6. The main menu appears immediately and asks what you'd like to do.

### Running the automated tests

The test suite (`tests/`) uses `pytest` and needs no setup beyond the
`pip install -r requirements.txt` step above — it builds its own temporary,
throwaway database for each test (see `tests/conftest.py`), so it never touches
your real `ncrs_database.sqlite3` file. From the project folder, run:
```
pytest
```
All tests are expected to pass (86 tests at the time of writing) before any
change is considered complete — see `docs/03_maintenance_and_support_plan.md`
section 2.3 for how this fits into the project's maintenance workflow. This
`pytest` run only ever collects the CLI's test suite in `tests/` — the web
interface has its own, separate manual check script (section 3.5), so
running `pytest` never starts a web server or touches a browser.

### Navigation conventions (CLI only — the web interface uses ordinary page buttons/links instead)
- `0` — Back / Logout / Exit
- `00` — Reset test data (Super Administrator only, with a Yes/No confirmation)
- `H` — Show a short Help message for the current menu (available at any prompt)
- `C` — Cancel the current multi-step operation (e.g. abort a booking mid-entry)
  and return to the previous menu, without logging out
- `Ctrl+C` — Safely exit the program at any time, from anywhere

These are handled consistently by one shared input-handling function, so every menu
in the system understands the same set of commands rather than each screen
inventing its own rules. Every screen's result (success or error) is shown with a
"Press Enter to continue..." pause (`cli/common.show_success()` /
`cli/common.show_error()`) so it always stays on screen long enough to read, rather
than being immediately overwritten by the next menu redraw.

## 3. Web Interface (Optional Addition)

`web/app.py` is a small [Flask](https://flask.palletsprojects.com/) web application
that gives NCRS a second, browser-based way to run, added after the CLI was already
complete, tested, and documented. It is **not** a replacement for the CLI — both keep
working, independently, against the same database.

**Why it's safe alongside everything above:** every action in `web/app.py` (logging
in, registering, adding a vehicle, confirming a booking, recording a payment...) calls
the exact same `services/*.py` functions the CLI already calls. No business rule,
validation, or pricing formula was duplicated or rewritten to build this — the web
pages are a thin "front end" over the same rules described throughout this README,
so behaviour is identical either way.

### 3.1 How to run it (step-by-step, including VS Code)

The two most common ways this goes wrong are (a) opening `requirements.txt` itself
and pressing "Run" — that file is just a plain text list, not a program, so nothing
happens — and (b) `pip install` running against a *different* Python than the one
that later runs `web/app.py`, so Flask ends up "installed" somewhere the app can't
see. The steps below avoid both:

1. In VS Code, open **Terminal → New Terminal** (this opens a terminal already
   sitting in this project's folder — don't use the "Run Python File" ▷ button on
   `requirements.txt` or `app.py`, always use the terminal for these two commands).
2. **If this project has a `.venv` folder** (it does, from earlier `pytest` setup):
   make sure that same environment is active before installing anything. VS Code
   usually activates it automatically and shows `(.venv)` at the start of the
   terminal prompt; if you don't see `(.venv)`, run:
   ```
   .venv\Scripts\activate
   ```
   (On the same terminal you'll use for every command below — installing into one
   Python and running `python web/app.py` with another is exactly what causes
   `ModuleNotFoundError: No module named 'flask'`.)
3. Install the third-party packages (see section 5):
   ```
   pip install -r requirements.txt
   ```
4. Run the web app from the **project's root folder** (`Car_Rental_MIS`, not
   inside `web/`):
   ```
   python web/app.py
   ```
5. Watch the terminal output. A working start looks like this:
   ```
   Starting Nepal Car Rental System (NCRS) web interface...
   Open http://127.0.0.1:5000 in your browser. Press CTRL+C to stop.
   ...
    * Running on http://127.0.0.1:5000
   ```
   The `* Running on http://127.0.0.1:5000` line is the important one — it means
   the server is actually up. If instead you see a red error (most commonly
   `ModuleNotFoundError: No module named 'flask'`, or `'python' is not recognized`),
   the app never started — go back to step 2/3 and fix that first; opening a
   browser will not help until this line appears.
6. Your **default browser should open to the site automatically** a second or two
   after step 5 (this is done for you — see the code comment above `app.run()` in
   `web/app.py`). If it doesn't open by itself, open any browser yourself and type
   (not search) this into its address bar:
   ```
   http://127.0.0.1:5000
   ```
   Nothing else opens it — not double-clicking `app.py`, not a search engine, and
   not a file path like `C:\...\web\app.py`. `127.0.0.1` ("localhost") always
   means "this computer", so this is completely offline; no internet connection
   is used or needed.
7. Leave the VS Code terminal running in the background while you use the site —
   closing it (or pressing `Ctrl+C`) stops the web server and the pages will stop
   loading. Press `Ctrl+C` in that terminal to stop it on purpose when you're done.

The very first time either `main.py` or `web/app.py` is run, the database is created
and seeded automatically (see section 4) — it doesn't matter which one you start
with first.

**No password to remember for a demo:** the Login page itself now shows a
"Demo Accounts" box with a one-click **Log in as...** button for each of the
three roles (Super Administrator / Vehicle Owner-Driver / Customer) — see
section 4 below for the same three accounts and their passwords in full.

### 3.2 What's in the web interface

Every page from the CLI has a browser equivalent, using the same wording wherever
possible:

- **Public pages (no login):** Home, Login, Register (Super Administrator / Vehicle
  Owner-Driver / Customer), Forgot Password, Browse Available Vehicles, Vehicles by
  Car Type, Rental Information, About.
- **Super Administrator dashboard:** Manage Users + reset a password, Pending
  Registrations (approve/reject), All Vehicles + update status, Manage Bookings
  (confirm/reject/cancel/complete, filter by status), Payments (record + view all),
  System Statistics, Set Rate per KM, Change My Password, Reset Test Data.
- **Vehicle Owner/Driver dashboard:** My Vehicles, Add a New Vehicle, Edit a
  Vehicle (update rate / update status / delete), View a Vehicle's Waitlist, Change
  My Password.
- **Customer dashboard:** Browse/Search Vehicles, Book a Vehicle (with the same
  driver-hire option and the same "conflict → join the waitlist instead" flow as the
  CLI), My Bookings (cancel / pay), Join a Vehicle's Waitlist directly, Change My
  Password.

### 3.3 How login works on the web (different from the CLI, same rules)

The CLI keeps the logged-in user's details in memory for as long as that dashboard's
menu loop keeps running. A web browser can't do that — every click is a brand new,
independent request with no memory of the last one. The standard fix, used here, is
a **session cookie**: after a successful login, the browser is given a small, signed
cookie containing nothing but the account's internal ID number (never a password).
On every later page load, `web/app.py` reads that ID back out and rebuilds the real
account object fresh from the database (a small helper added for this,
`auth_service.get_user_by_id()` — the only new function added to the `services/`
layer for the whole web interface; everything else it calls already existed for the
CLI). The role-based access rules are exactly the CLI's: an Owner/Driver can never
edit or delete a vehicle they don't own, a Customer can never pay for or cancel
someone else's booking, and only a Super Administrator can reach the `/admin/...`
pages — enforced the same way (`role_required()` in `web/app.py`, mirroring
`isinstance()` dispatch in `cli/public_menu.py`).

### 3.4 Files added for the web interface

| File / Folder | Purpose |
|---|---|
| `web/app.py` | The Flask application: every route (URL → Python function), session/login handling, and the mapping from each page to the matching `services/*.py` call. No business logic lives here — see section 3 above. |
| `web/templates/` | 27 HTML page templates (Jinja2 — Flask's templating language), one per screen, all extending `base.html` for a shared header/navigation/flash-message layout. |
| `web/static/style.css` | One shared, plain CSS file (no framework, no build step) for every page — colours match the CLI/report branding (Himalayan blue, Nepal-flag red used sparingly). |
| `web/manual_web_check.py` | An end-to-end manual smoke-test script for the web pages themselves (see section 3.5) — separate from, and not counted in, the 86 `pytest` tests in section 2. |

### 3.5 Verifying the web interface

`web/manual_web_check.py` clicks through every major page and action (register,
login as each of the three roles, add/edit/delete a vehicle, book a vehicle, hit a
booking conflict and join the waitlist, record a payment, approve a pending
registration, reset a password, and confirm the ownership/access-control rules are
enforced) using Flask's own test client — no real browser or network port needed.
Run it any time after changing anything under `web/`:
```
python web/manual_web_check.py
```
A clean run ends with `TOTAL FAILURES: 0`. This script is intentionally **not**
named so that plain `pytest` picks it up (see the note at the end of section 2) —
it is a separate, manual check for the web layer, kept apart from the CLI's own
automated `tests/` suite so that suite's "86 tests" count (quoted throughout this
project's documentation and report) never silently changes.

### 3.6 Known limitation of the web interface

Flask's built-in server prints a standard warning on startup
(`WARNING: This is a development server. Do not use it in a production
deployment.`) — this is expected and fine for this project: NCRS is designed to run
on the student's own computer only (NFR1/NFR2 — fully offline, no real deployment),
never on a public server, so Flask's simple built-in server is the right tool, not
a limitation in practice.

## 4. Demo Login Credentials

On first run, the program automatically seeds the database with realistic sample
data (10 vehicles, 3 bookings, a waitlist entry, payments, etc.) so there is
something to explore immediately, with no manual setup. The full seeded dataset is
documented in `docs/02_seed_data_plan.md`; the accounts below are the quickest way
in — they work identically whether you log in from the CLI or from the web interface.

**On the web interface, you don't need to type any of this at all** — the Login
page (`http://127.0.0.1:5000/login`) shows a "Demo Accounts" box with a one-click
**Log in as...** button for the Super Administrator, Vehicle Owner/Driver, and
Customer accounts below, for quick demos/marking. The CLI still needs the
username/password typed in as usual.

| Role | Username | Password | Try this after logging in |
|---|---|---|---|
| Super Administrator | `admin_ncrs` | `Admin@123` | View the full vehicle list (10 vehicles across every status/type), approve `owner_hari`'s pending registration, view all bookings/payments, view/update the NZD$ rate per km, view all users (passwords masked) and reset one |
| Vehicle Owner/Driver (approved) | `owner_ram` | `Owner@123` | View/manage the vehicles he owns and their bookings |
| Vehicle Owner/Driver (pending) | `owner_hari` | `Owner@123` | Try logging in before admin approves — should be rejected; works after admin approves the account |
| Hired driver | `driver_bikash` | `Driver@123` | Appears as the assigned driver on Booking A (Tucson) |
| Customer | `customer_sita` | `Customer@123` | View her CONFIRMED upcoming Tucson booking and her COMPLETED past Corolla booking + payment history |
| Customer | `customer_gita` | `Customer@123` | View her ACTIVE Scorpio rental, AND her waitlist entry for the Tucson — cancel/complete `customer_sita`'s Tucson booking (as admin) to see her get auto-notified |

You can also browse **View Available Cars** and **View Car Types** from the main
menu (or the web interface's Home page) without logging in at all — no account
needed for that.

## 5. Third-Party Packages Used

This project is kept deliberately lightweight and runs fully offline. Everything is
free and open-source — no paid packages, no paid APIs, no subscriptions.

| Package | Version | What it's used for | How to install |
|---|---|---|---|
| [`tabulate`](https://pypi.org/project/tabulate/) | 0.9.0 | Formats data (vehicle lists, booking lists, reports) as clean text tables in the CLI, instead of hand-aligning columns with spaces | `pip install -r requirements.txt` (or `pip install tabulate`) |
| [`pytest`](https://pypi.org/project/pytest/) | 8.3.3 | Runs the automated test suite in `tests/` (validation rules, booking conflict detection, cost calculation, waitlist notifications) | `pip install -r requirements.txt` (or `pip install pytest`), then run tests with `pytest` |
| [`Flask`](https://pypi.org/project/Flask/) | 3.1.3 | Powers the OPTIONAL web interface (`web/app.py` — see section 3) — routing, HTML templating, and session/login cookies. Only needed if you want to run the web interface; `main.py` never imports it | `pip install -r requirements.txt` (or `pip install Flask`), then run with `python web/app.py` |

Everything else uses only Python's own standard library (e.g. `sqlite3` for the
database, `datetime` for dates) — nothing else needs to be installed.

## 6. Custom Decorator — Authorship Tagging

`utils/author_decorator.py` defines a custom decorator, `author_info(name,
student_id, institution)`, applied to the project's key classes (for example
`RentalSystem`). It attaches the developer's name, student ID, and institution as
real attributes on the class itself (e.g. `RentalSystem.__author__`), so the CLI's
"About Nepal Car Rental System" screen (and the web interface's About page) reads
this information directly from the running code rather than from a comment. This
doubles as a practical demonstration of the Decorators topic from the course
material, applied to a genuine use case rather than a toy example.

## 7. Project Files

| File / Folder | Purpose |
|---|---|
| `main.py` | CLI entry point. Boots the `RentalSystem` singleton, shows the welcome menu, and safely handles Ctrl+C. |
| `config.py` | Central configuration constants: assignment/course/student details, registration keywords, currency symbol, default rate per km, database file name. |
| `requirements.txt` | The third-party packages this project uses (see section 5) and their exact versions. |
| `.gitignore` | Keeps generated files (`__pycache__/`, the SQLite database, `.venv/`) out of version control. |
| **`models/`** | The OOP domain classes — the data + business rules, with no database or CLI/web code. |
| `models/user.py` | `User` base class plus `Admin`, `VehicleOwnerDriver`, `Customer` subclasses (inheritance + polymorphism). |
| `models/vehicle.py` | `Vehicle` — also the "Subject" side of the Observer pattern (`notify_waitlist()`). |
| `models/booking.py` | `Booking` — status lifecycle (`confirm()`/`cancel()`/`complete()`) and the `calculate_cost()` pricing formula. |
| `models/payment.py` | `Payment` — a simple record of one simulated payment against a booking. |
| `models/observer.py` | `Observer` — the abstract interface for the Observer pattern. |
| `models/waitlist.py` | `WaitlistEntry` — the concrete "Observer" that reacts when a vehicle becomes available. |
| **`services/`** | Business logic. Every rule about *what is allowed* lives here, not in the CLI or the web layer — this is what makes it safe for both front ends to share. |
| `services/auth_service.py` | Login, the three registration flows, self-service and admin password resets, and `get_user_by_id()` (added for the web interface's session handling — see section 3.3). |
| `services/vehicle_service.py` | Vehicle CRUD, searching, and browsing. |
| `services/booking_service.py` | Booking creation, availability/conflict checking, cost calculation, and the status lifecycle. |
| `services/waitlist_service.py` | Joining a waitlist and the FIFO auto-notify logic (the Observer pattern's "notify" step). |
| `services/payment_service.py` | Recording and listing simulated payments. |
| `services/admin_service.py` | Registration approval/rejection, the masked user list, system statistics, and "Reset Test Data". |
| `services/rental_system.py` | `RentalSystem` — the Singleton that boots the database and seed data (decorated with `@author_info`). |
| **`database/`** | Everything to do with persistence (SQLite). |
| `database/db_connection.py` | `DatabaseConnection` — the Singleton wrapping the one shared SQLite connection. |
| `database/schema.py` | `CREATE TABLE` statements for every table. |
| `database/seed_data.py` | Inserts the ~29-row demo dataset the first time the database is empty (see section 4 and `docs/02_seed_data_plan.md`). |
| **`cli/`** | The text menus the user actually sees and types into. |
| `cli/common.py` | Shared input handling (`read_input`, `read_menu_choice`, `confirm_yes_no`) and the shared `show_success()`/`show_error()` result screens (which always pause for "Press Enter to continue..." so the outcome is never missed) — so every CLI screen understands the same navigation commands and reports its outcome the same way. |
| `cli/public_menu.py` | The welcome screen (login/register/browse/about), and role dispatch after a successful login. |
| `cli/auth_menu.py` | Login, forgot-password, and the three registration sub-flows. |
| `cli/about_screen.py` | The "About" screen — academic details + live `@author_info` decorator metadata. |
| `cli/customer_menu.py` | The Customer dashboard: browse, search, book, pay, join a waitlist, change password. |
| `cli/owner_menu.py` | The Vehicle Owner/Driver dashboard: manage own vehicles, view own waitlists. |
| `cli/admin_menu.py` | The Super Administrator dashboard: users, registrations, bookings, payments, statistics, rate-per-km, "00 Reset Test Data". |
| **`web/`** | The optional browser-based interface — see section 3 for full detail. |
| `web/app.py` | The Flask application and every page's route. |
| `web/templates/` | The 27 HTML page templates. |
| `web/static/style.css` | The shared page styling. |
| `web/manual_web_check.py` | The web interface's own end-to-end manual check script (section 3.5). |
| **`utils/`** | Small, shared, dependency-free helper functions. |
| `utils/validators.py` | Every input-checking rule used across the whole CLI (and reused by the web interface). |
| `utils/security.py` | Salted password hashing/verification and temporary-password generation. |
| `utils/formatters.py` | Currency formatting, table formatting (via `tabulate`), and the masked-password placeholder. |
| `utils/author_decorator.py` | The custom `@author_info` decorator (see section 6). |
| **`tests/`** | The automated test suite (`pytest`) — see "Running the automated tests" in section 2. |
| `tests/conftest.py` | The `clean_database` fixture: a fresh, temporary, pre-seeded database for every test. |
| `tests/test_validators.py` | Tests for every validation rule (good input accepted, bad input rejected). |
| `tests/test_security.py` | Tests for password hashing/verification. |
| `tests/test_booking_cost.py` | Tests for the pricing formula and the booking status lifecycle. |
| `tests/test_booking_conflict.py` | Tests for date-overlap/availability checking and booking creation. |
| `tests/test_auth_and_password_reset.py` | Tests for login, registration, and both password-reset flows. |
| `tests/test_vehicle_and_admin_service.py` | Tests for vehicle CRUD and admin-only actions. |
| `tests/test_waitlist_notify.py` | Tests for the Smart Waitlist + Auto-Notify (Observer pattern) feature. |
| **`docs/`** | Design and planning documents produced before any code was written. |
| `docs/01_requirements_analysis.md` | The full requirements analysis (functional/non-functional requirements, business rules, architecture). |
| `docs/02_seed_data_plan.md` | The exact demo dataset seeded into the database (see section 4). |
| `docs/03_maintenance_and_support_plan.md` | Task 3: the maintenance, versioning, and backward-compatibility plan. |
| `docs/diagrams/` | The 5 UML/ER diagrams (Use Case, Class, 2x Sequence, ER) as editable `.drawio` files (open with [diagrams.net](https://app.diagrams.net/)). |

## 8. Known Bugs / Issues

No crashing bugs are known at the time of writing — every screen was manually
walked through end-to-end on both the CLI (login, registration for all 3 roles,
booking with and without a driver, cancelling, payments, joining a waitlist, the
Observer auto-notify firing, admin approval/rejection, password resets, and "00
Reset Test Data") and the web interface (`web/manual_web_check.py`, section 3.5),
and the full `pytest` suite (86 tests) passes. A few known, deliberate limitations
remain, appropriate for an academic project of this scope:

- **A previously-reported CLI bug is now fixed:** registering a new account (or any
  other action) used to print its success/error message and then immediately fall
  straight back into the next menu's redraw, so the message could look like it had
  scrolled away unseen. `cli/common.show_success()` and `show_error()` now always
  pause with "Press Enter to continue..." before returning, so every action's
  outcome is guaranteed to be seen. Because the whole CLI shares these two
  functions, this one fix applies everywhere at once (login, registration,
  password changes, adding/updating/deleting a vehicle, every booking action,
  payments, and so on) — see the comments in `cli/common.py` for the full
  explanation.
- **No real payment gateway, email, or SMS.** Payments and waitlist
  notifications are simulated and printed to the console (see
  `services/payment_service.py` and `models/waitlist.py`) — this is intentional
  (see `docs/01_requirements_analysis.md`'s "Out of scope" list), not a bug.
- **No pagination for very large tables.** If the fleet grew into the hundreds
  of vehicles, `utils/formatters.format_table()` (CLI) or the web interface's
  plain HTML tables would show them all at once rather than paging through them.
  Not an issue at the current demo scale (10 vehicles).
- **`Y`/`N` vs `1`/`2` for Yes/No prompts (CLI only).** Most confirmations in the
  CLI use numbered `1. Yes` / `2. No` menus (`cli/common.confirm_yes_no()`), while
  a couple of screens use a typed `Y`/`N` (e.g. "Do you need a driver?"). Both are
  intentional, consistent within their own screen, and explained by the prompt
  text itself — not a functional bug, just worth knowing about when using the
  system. The web interface uses an ordinary checkbox for the same question
  instead, since there is no keyboard-shortcut convention to match there.
- **SQLite over a cloud-synced or network-mounted folder.** SQLite needs real
  file locking to work reliably. If this project folder is ever moved onto a
  network drive, or an "online-only" cloud-sync folder (some OneDrive/Dropbox
  configurations), running the CLI or the web interface can fail with
  `sqlite3.OperationalError: disk I/O error`. Running it from a normal local
  folder on your own hard drive (as `D:\Car_Rental_MIS` already is) avoids this
  entirely.
- **A vehicle can be deleted once every booking against it has finished.**
  `vehicle_service.delete_vehicle()` deliberately blocks deletion while a
  PENDING/CONFIRMED/ACTIVE booking exists, but allows it once all of a
  vehicle's bookings are COMPLETED/CANCELLED/REJECTED. A customer's own
  booking history screen (CLI and web) handles this gracefully (it shows
  "(vehicle no longer in system)" instead of failing), but it is worth knowing
  this is possible - a real production system would more likely soft-delete
  (archive) a vehicle instead of removing its row outright.
- **The web interface's session cookie uses a fixed local secret key.** Fine for
  this project's purpose (a single student's own computer, never deployed
  publicly — see section 3.6), but a real production deployment would read this
  from an environment variable instead of the hard-coded value currently in
  `web/app.py`. Flagged in a comment right above that line in the code.

## 9. Licence

Released under the **MIT Licence** — a short, permissive open-source licence
chosen as a sensible default for an academic assignment: it lets the lecturer,
marker, or anyone else freely run, read, and reuse this code (with attribution),
while placing no warranty obligations on the student author.

> Copyright (c) 2026 Anish Shrestha
>
> Permission is hereby granted, free of charge, to any person obtaining a copy of
> this software and associated documentation files (the "Software"), to deal in
> the Software without restriction, including without limitation the rights to
> use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
> the Software, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
> FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

The full licence text is also available in the standalone `LICENSE` file in this
repository.

## 10. Credits

Developed by **Anish Shrestha** (Student ID: 270889991) for **Assessment 1** of
**Professional Software Engineering (MSE-800)**, part of the **Master of Software
Engineering** programme at **Yoobee College, New Zealand**, under the supervision of
**Mohammad Norouzifard**.
