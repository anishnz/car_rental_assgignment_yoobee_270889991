# Nepal Car Rental System (NCRS) — Requirements Analysis

**Programme:** Master of Software Engineering — 180 Credits
**Course:** Professional Software Engineering (MSE-800) — Level 8, 15 Credits, Version 1
**Assessment:** Assessment 1 — Object-Oriented Programming Assignment (30%, Individual)
**Lecturer:** Mohammad Norouzifard
**Student Name:** Anish Shrestha
**Student ID:** 270889991
**Institution:** Yoobee College, New Zealand
**Document status:** DRAFT v1 — for review and approval before design/coding begins

---

## 1. Project Overview

Nepal Car Rental System (NCRS) is a Python command-line application that automates the
rental process for a car rental business operating in Nepal. It replaces manual,
paper-based booking with a menu-driven CLI backed by a local SQLite database, covering
customer and vehicle-owner/driver registration, vehicle and driver management, rental
booking with availability checking, rental cost calculation, a simulated payment record,
and administrator approval workflows.

The project exists to satisfy MSE800 Assignment 1: demonstrate object-oriented
programming, appropriate design patterns, and sound software engineering practice by
building a small but complete and defensible system — not a commercial-grade product.

## 2. Problem Statement

A car rental company currently relies on manual paperwork to register customers, track
vehicle and driver availability, record bookings, and calculate charges. This process is
slow, error-prone (e.g. double-booking a vehicle for overlapping dates), and gives
management no easy way to see pending requests, active rentals, or revenue. The company
needs a simple, reliable software system that any staff member can run locally, without
depending on the internet or a paid third-party service, to manage the end-to-end rental
process correctly and consistently.

## 3. Aim

To design and implement a Python-based, object-oriented Car Rental Management System
(themed for the Nepalese market) that manages users, vehicles, drivers, bookings, and
payments through a CLI, using a local SQLite database, while demonstrating sound OOP
design, validation, and at least one design pattern beyond the basics.

## 4. Objectives

1. Implement user registration and authentication for three roles: Super Administrator,
   Vehicle Owner/Driver, and Customer.
2. Manage vehicle records (add/update/delete/search) with status tracking.
3. Manage driver records (add/update/delete/search) with status tracking.
4. Allow customers to browse available vehicles and car types without logging in.
5. Allow customers to book a vehicle for a date range, with automatic validation of
   dates and detection of booking conflicts (overlapping date ranges).
6. Calculate rental cost automatically (day-based vehicle cost + distance-based
   cost using an admin-configurable rate per km + optional driver cost).
7. Allow administrators to approve or reject registration and booking requests.
8. Persist all data in a local SQLite database bundled with the project (no server
   install, no internet required).
9. Validate all user input and handle errors gracefully (the program must never crash
   on bad input).
10. Demonstrate OOP concepts: classes, objects, constructors, encapsulation,
    inheritance, polymorphism, abstraction, and composition.
11. Demonstrate the **Observer design pattern** through an innovative Smart Waitlist +
    Auto-Notify feature (see section 9).
12. Provide clear ReadMe and Maintenance/Support documentation as required by the
    marking rubric.

## 5. Scope

### In scope
- CLI-only application (no GUI, no web interface).
- Three user roles: Super Administrator, Vehicle Owner/Driver, Customer.
- Registration with role-specific keywords; admin approval workflow for Vehicle
  Owner/Driver accounts and for bookings.
- Vehicle CRUD, Driver CRUD, Customer records, Booking CRUD, simulated Payment records.
- Booking availability / date-overlap conflict detection.
- Rental cost calculation (vehicle rate x days, PLUS distance in km x an
  admin-configurable rate per km, PLUS optional driver rate x days).
- Smart Waitlist + Auto-Notify innovative feature (Observer pattern).
- Local SQLite database, created automatically on first run.
- Password reset simulated with a keyword (no real email/SMS).
- Automated tests for core logic (validation, availability, cost calculation, waitlist).
- ReadMe and Maintenance & Support documentation.

### Out of scope (deliberately excluded to keep the assignment academically appropriate)
- Real payment gateways, GPS tracking, mobile apps, AI chatbots, blockchain,
  microservices, Kubernetes, real SMS/email gateways, complex accounting, dynamic
  pricing, insurance processing, facial recognition, real driving-licence verification.
- Any paid third-party API or AI service.
- Any requirement for an internet connection or externally hosted database.
- A Flask/web interface (may be considered only as a future enhancement, not part of
  this submission).

## 6. Stakeholders

- **Anish Shrestha** — student/developer, responsible for design, implementation, and
  submission.
- **Course lecturer / marker** — evaluates the system against the MSE800.1 rubric.
- **End users (simulated by the system's roles)** — Super Administrator, Vehicle
  Owner/Driver, Customer — represented as CLI actors during demonstration and testing.

## 7. User Roles

| Role | Description | Key Permissions |
|---|---|---|
| Super Administrator | Manages the whole system | Approve registrations/bookings, manage vehicles, drivers, customers, view all bookings/payments, view reports, reset test data |
| Vehicle Owner / Driver | Owns/drives vehicles listed on the platform | Manage own vehicles, view own bookings, manage own driver profile (registration requires admin approval) |
| Customer | Rents vehicles | Browse/search vehicles, book a vehicle, view/cancel own bookings, join a waitlist, view own payment info |

Rule: a user must log in before accessing any private or role-specific function. Public,
unauthenticated access is limited to browsing available vehicles, car types, and general
rental information.

## 8. Functional Requirements

**User Management**
- FR1: The system shall allow new users to register as Super Administrator, Vehicle
  Owner/Driver, or Customer, each requiring a role-specific registration keyword.
- FR2: The system shall allow registered users to log in with a username and password.
  Passwords shall be stored as a salted hash (never in plain text); logging in
  compares the hash of the entered password against the stored hash.
- FR3: The system shall support a simulated self-service password-reset flow using a
  reset keyword.
- FR4: Vehicle Owner/Driver accounts shall remain in a PENDING state until an
  administrator approves them.
- FR4a: The Super Administrator shall be able to view a list of all users (username,
  role, status) with each password shown only as a masked placeholder (e.g.
  `****** (hashed)`), since a hashed password can never be reversed back to its
  original value.
- FR4b: The Super Administrator shall be able to reset any user's password directly
  (entering a new password, or having the system generate one). The new password is
  hashed and saved immediately, and shown once on screen right after the reset so the
  administrator can pass it on to the user.

**Vehicle Management**
- FR5: Administrators (and vehicle owners, for their own vehicles) shall be able to add,
  update, and delete vehicle records.
- FR6: The system shall track vehicle status: AVAILABLE, BOOKED, RENTED, MAINTENANCE.
- FR7: Any user (including unauthenticated visitors) shall be able to view available
  vehicles and browse by car type.

**Driver Management**
- FR8: Administrators shall be able to add, update, and delete driver records.
- FR9: The system shall track driver status: AVAILABLE, ASSIGNED, OFF_DUTY.

**Booking Management**
- FR10: Customers shall be able to request a booking by specifying a vehicle, pickup
  date, return date, estimated distance to be travelled (in km), and whether a
  driver is required.
- FR11: The system shall reject a booking if the return date is not after the pickup
  date, or if either date is invalid.
- FR12: The system shall reject a booking if the vehicle is already booked for any
  overlapping date range.
- FR13: The system shall calculate and display the total rental cost before the
  customer confirms the booking, as: (Days x Daily Vehicle Rate) + (Distance in km x
  Rate per km) + (Days x Driver Daily Rate, if a driver is requested). All amounts
  are shown in New Zealand Dollars (NZD$).
- FR13a: The Super Administrator shall be able to view and update the system-wide
  rate per kilometre (default NZD$5.00/km) used in the distance-based part of the
  cost calculation. This value is stored in the database, not hard-coded, so it can
  be changed at any time without editing code.
- FR14: Administrators shall be able to approve or reject pending booking requests.
- FR15: On booking completion or cancellation, the system shall update the vehicle
  (and driver, if assigned) status back to AVAILABLE.

**Waitlist (Innovative Feature)**
- FR16: If a requested vehicle is unavailable for the requested dates, the customer
  shall be offered the option to join a waitlist for that vehicle.
- FR17: When a vehicle's status changes to AVAILABLE, the system shall automatically
  check its waitlist and notify the next waiting customer (in FIFO order) via a
  console/log notification.

**Payment**
- FR18: The system shall record a simulated payment against a booking, including
  amount, method (CASH/CARD/BANK_TRANSFER), and status (PENDING/PARTIAL/PAID).

**Reporting**
- FR19: Administrators shall be able to view lists of customers, drivers, vehicles,
  bookings (all/completed/cancelled), and payments, and basic system statistics.

## 9. Innovative Feature — Smart Waitlist + Auto-Notify

Chosen to satisfy the rubric's Task 2 requirement for "an innovative feature or
enhancement that sets your car rental system apart from traditional systems," while
staying within CLI/offline scope.

- Implements the **Observer design pattern**: a vehicle (the Subject) maintains a list
  of waitlisted customers (Observers). When the vehicle's status changes to AVAILABLE
  (booking completed, cancelled, or rejected), it notifies the next customer(s) in its
  waitlist queue.
- Implements a **FIFO queue** per vehicle for waitlist ordering — a clear, simple
  algorithmic component distinct from the booking-conflict-detection algorithm.
- Notification is simulated (printed to the console and/or written to a local
  notifications log file) — no real email/SMS, consistent with the "no internet, no
  paid services" constraint.

## 10. Non-Functional Requirements

- NFR1: The application shall run entirely offline, with no dependency on internet
  access or any external/cloud service.
- NFR2: The application shall use no paid third-party API or AI service.
- NFR3: The application shall use a local SQLite database file bundled with the
  project; no separate database server installation shall be required.
- NFR4: The entire project shall be deliverable as a single zip folder; running the
  main file shall start the whole application and immediately present the interactive
  CLI menu, with no additional setup steps.
- NFR5: The system shall not crash on invalid input; all user input shall be validated
  and errors handled with clear, user-friendly messages.
- NFR6: The codebase shall follow consistent naming, indentation, and formatting
  conventions (PEP 8) and shall be organised into modular files/packages.
- NFR7: Every class and function shall include a docstring/comment explaining what it
  does, why it exists, and how it is used, so the code is understandable to any reader,
  including during debugging.
- NFR8: The system shall respond to Ctrl+C by catching `KeyboardInterrupt`, printing a
  clean shutdown message, and exiting safely rather than crashing.

## 11. Business Rules

- BR1: A Vehicle Owner/Driver account cannot be used to log in until approved by an
  administrator.
- BR2: A vehicle cannot have two CONFIRMED/ACTIVE bookings with overlapping date
  ranges.
- BR3: Rental cost = (number of days x vehicle daily rate) + (estimated distance in
  km x the current admin-set rate per km). If a driver is requested, driver cost =
  number of days x driver daily rate is added on top. All monetary values are shown
  in NZD$ (New Zealand Dollars).
- BR3a: Only an administrator may change the rate per km; the new rate applies to
  bookings made after the change (bookings already confirmed keep the rate that was
  in effect when they were calculated).
- BR4: A booking cannot be confirmed without administrator approval.
- BR5: Only an administrator may delete a driver or reset test data, and both actions
  require explicit confirmation (Yes/No) before proceeding.
- BR6: A customer may only view or cancel their own bookings, never another
  customer's.

## 12. Assumptions

- A single computer runs the system locally for demonstration; multi-user concurrent
  access is not required.
- Currency is NZD$ (New Zealand Dollar) for all cost displays and calculations; this
  is a display convention (a fixed currency symbol, not a live exchange-rate
  feature), chosen because Anish is studying in New Zealand, even though the
  vehicles/branding are Nepal-themed.
- The registration keywords (e.g. `admin`, `vehicle_Owner_Driver`, `customer`,
  `password_rest`) are placeholders suitable for an academic demo, stored as
  configuration values rather than hard-coded throughout the code.
- The "release build" required by the submission checklist is a packaged/zipped copy of
  the working Python source (this is a script-based CLI tool, not a compiled
  executable), unless Anish decides to package it with a tool such as PyInstaller.

## 13. Constraints

- Must be implemented in Python 3 using only the standard library plus, at most,
  lightweight, free, offline-friendly packages (e.g. `tabulate` for table formatting) —
  no paid packages or services.
- Must not require MySQL or any other external database server (SQLite only).
- Must be demonstrable and explainable by Anish individually (no group dependency; this
  is an individual assignment).
- Must be completed by the Week 7 deadline for MSE800.1.

## 14. Main Modules

| Module | Responsibility |
|---|---|
| `main.py` | Application entry point; boots the system and shows the main CLI menu |
| `config.py` | Configuration values (registration keywords, file paths, constants) |
| `database/` | SQLite connection handling and schema initialisation |
| `models/` | OOP domain classes: `User`, `Admin`, `VehicleOwnerDriver`, `Customer`, `Vehicle`, `Driver`, `Booking`, `Payment`, `Waitlist` |
| `services/` | Business logic: authentication, registration/approval, vehicle & driver management, booking & availability logic, cost calculation, waitlist/Observer notifications, payment recording |
| `cli/` | Menu screens and input/output handling for each role |
| `utils/` | Shared helpers: input validation, date handling, formatting |
| `tests/` | Automated tests for validation, availability/conflict detection, cost calculation, and waitlist behaviour |
| `docs/` | Requirements, design diagrams, ReadMe, maintenance plan |

## 15. Main Use Cases

- Register (as Super Administrator / Vehicle Owner-Driver / Customer)
- Login / Logout
- Reset Own Password (self-service, via reset keyword)
- Browse Available Vehicles / View Car Types (public)
- Search Vehicle
- Book a Vehicle
- Join Waitlist for a Vehicle
- Receive Waitlist Notification (system-triggered)
- Cancel Booking
- View My Bookings / View My Payments
- Approve/Reject Registration Request (Admin)
- Approve/Reject Booking Request (Admin)
- View All Users with Masked Passwords (Admin)
- Reset Any User's Password (Admin)
- Set/Update Rate per KM (Admin)
- Add/Update/Delete Vehicle
- Add/Update/Delete Driver
- Record Payment
- View Reports / System Statistics
- Reset Test Data (Admin only)

(A full Use Case Diagram will be produced in the design phase — see section 16.)

## 16. Required Diagrams (design phase — next step, not yet produced)

- Use Case Diagram
- Class Diagram
- Sequence Diagram (at least for the booking + waitlist-notify flow)
- Entity-Relationship (ER) Diagram for the SQLite schema
- Optional supporting sketches: DFD Level 0/1, system flowchart, high-level
  architecture diagram — useful for Task 1's "high-level architectural diagram and
  description of how each component interacts."

Diagrams will be authored as editable `.drawio` XML files (openable directly in
diagrams.net / draw.io, desktop or web, for further editing) and also previewed as
Mermaid diagrams in chat for quick review before finalising.

**Status: produced.** Located in `docs/diagrams/`:
- `01_use_case_diagram.drawio`
- `02_class_diagram.drawio`
- `03_sequence_diagram_booking.drawio`
- `04_sequence_diagram_waitlist_notify.drawio`
- `05_er_diagram.drawio`

Open any of these in https://app.diagrams.net (or the draw.io desktop app) to view,
rearrange, or export as an image for the submission PDF.

## 17. Proposed Database Entities (SQLite)

- `users` (id, username, password_hash, role, status)
- `customers` (id, user_id, full_name, phone, email, address, licence_no)
- `vehicle_owners_drivers` (id, user_id, full_name, phone, email, licence_no,
  licence_expiry, daily_driver_rate, status)
- `vehicles` (id, owner_id, registration_no, brand, model, year, vehicle_type, seats,
  daily_rate, status)
- `bookings` (id, customer_id, vehicle_id, driver_id, pickup_date, return_date,
  driver_required, distance_km, rate_per_km_applied, total_amount, status)
- `payments` (id, booking_id, amount, payment_date, method, status)
- `waitlist` (id, vehicle_id, customer_id, requested_pickup_date, requested_return_date,
  created_at, notified)
- `settings` (key, value) — system-wide configuration stored in the database rather
  than hard-coded, e.g. row `("rate_per_km", "5.00")`. Read whenever a booking cost is
  calculated, and updatable only by the Super Administrator (FR13a).

## 18. Recommended Architecture

A layered CLI application:

```text
cli/        -> presentation layer (menus, input/output)
services/   -> business logic layer (validation, booking rules, waitlist Observer logic)
models/     -> domain/OOP layer (entities and their behaviour)
database/   -> persistence layer (SQLite access)
```

Each layer depends only on the layer below it, which keeps the code modular and testable
and makes it straightforward to explain "what depends on what" during a viva.

## 19. Development Roadmap (recap)

See `assignment-1-decisions-and-roadmap` in the project knowledge base for the full
step-by-step process. Short version: this Requirements Analysis (step 2) -> Design &
diagrams (step 3) -> Database schema finalisation (step 4) -> Project scaffolding
(step 5, already begun) -> Incremental module-by-module build (step 6) -> CLI wiring
(step 7) -> Testing (step 8) -> Documentation (step 9) -> Final review & packaging
(step 10).

## 20. System Requirements (to run this project)

- Python 3.10 or later installed on the machine.
- No internet connection required.
- No external database server required (SQLite is built into Python's standard
  library).
- No paid API keys or subscriptions required.
- Recommended: VS Code (or any editor/terminal) to run the CLI.
- Optional dependencies (if any are used, e.g. `tabulate` for nicer table output) will
  be listed in `requirements.txt` and installed with a single `pip install -r
  requirements.txt` — kept minimal and free.

## 21. How to Run This Project (once built)

1. Extract the project zip (or open the folder) — no separate installation steps.
2. Open a terminal in the project folder (VS Code's integrated terminal works well).
3. (Optional, only if `requirements.txt` is non-empty) Run:
   `pip install -r requirements.txt`
4. Run the application:
   `python main.py`
5. On first run, the program automatically creates the local SQLite database file and
   required tables — no manual database setup.
6. The interactive main menu appears immediately, asking what you'd like to do (Login,
   Register, View Available Cars, etc.) — navigate using the on-screen menu numbers.
7. Press `0` at any menu to go back/log out/exit; `00` resets test data where
   permitted (Super Administrator only); `Ctrl+C` safely terminates the program at any
   time.

*(This section will be finalised and copied into the project's ReadMe once the actual
folder/file names are locked in during implementation.)*

---

**Next step:** Anish to review this document. Once approved (as-is or with changes),
we proceed to the design phase — Use Case, Class, Sequence, and ER diagrams.
