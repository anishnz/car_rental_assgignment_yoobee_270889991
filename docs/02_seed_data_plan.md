# NCRS — Demo Seed Data Plan

This document is the exact plan for the sample ("seed") data that will be inserted
automatically into the SQLite database the first time the program runs. It exists so
Anish (and the marker) always have realistic, ready-to-explore data without manually
registering accounts and adding vehicles first — and it is the specification the
actual seeding code (in `database/`, written during the build phase) will follow.

All demo passwords below are chosen by us before seeding, then hashed the same way any
real user's password would be (see FR2) — writing the plain-text value here does not
weaken the hashing; it just means we, the developers, wrote down the password we
ourselves picked for these fixed demo accounts, purely for convenience when marking or
demonstrating the system. This is normal practice for seed/demo accounts.

The `00 Reset Test Data` admin action restores the database to exactly this starting
set.

## 1. User Accounts (6)

| # | Role | Username | Password | Status | Notes |
|---|---|---|---|---|---|
| 1 | Super Administrator | `admin_ncrs` | `Admin@123` | ACTIVE | Full access to every admin function |
| 2 | Vehicle Owner/Driver | `owner_ram` | `Owner@123` | APPROVED | Owns most of the seeded vehicle fleet |
| 3 | Vehicle Owner/Driver | `owner_hari` | `Owner@123` | **PENDING** | Deliberately left pending, so Anish can demo the admin-approval workflow (FR4) live |
| 4 | Vehicle Owner/Driver (hired driver) | `driver_bikash` | `Driver@123` | APPROVED | Owns no vehicle; available to be assigned as a driver on bookings |
| 5 | Customer | `customer_sita` | `Customer@123` | ACTIVE | Has one CONFIRMED future booking and one COMPLETED past booking |
| 6 | Customer | `customer_gita` | `Customer@123` | ACTIVE | Has one ACTIVE booking (currently renting) AND one waitlist entry, to demo both features on one account |

## 2. Vehicle Fleet (10)

Covers every status and every car type in the "View Car Types" menu.

| # | Registration | Brand | Model | Type | Daily Rate (NZD$) | Owner | Status |
|---|---|---|---|---|---|---|---|
| 1 | BA 01 PA 1234 | Toyota | Corolla | Sedan | 65.00 | owner_ram | AVAILABLE |
| 2 | BA 02 PA 5678 | Hyundai | Tucson | SUV | 90.00 | owner_ram | BOOKED |
| 3 | BA 03 PA 8888 | Suzuki | Swift | Hatchback | 55.00 | owner_ram | AVAILABLE |
| 4 | BA 04 PA 2222 | Toyota | Hiace | Van | 110.00 | (admin-managed, no owner) | MAINTENANCE |
| 5 | BA 05 PA 3333 | Mahindra | Bolero | Jeep | 85.00 | owner_ram | AVAILABLE |
| 6 | BA 06 PA 4444 | Hyundai | Kona Electric | Electric Vehicle | 100.00 | owner_ram | AVAILABLE |
| 7 | BA 07 PA 5555 | Toyota | Land Cruiser Prado | Luxury Car | 180.00 | owner_ram | AVAILABLE |
| 8 | BA 08 PA 6666 | Kia | Sportage | SUV | 95.00 | owner_ram | AVAILABLE |
| 9 | BA 09 PA 7777 | Suzuki | Alto | Hatchback | 45.00 | owner_ram | AVAILABLE |
| 10 | BA 10 PA 9999 | Mahindra | Scorpio | Jeep | 88.00 | owner_ram | RENTED |

## 3. Drivers Available for Hire

`driver_bikash` — daily driver rate NZD$60.00, status AVAILABLE (becomes ASSIGNED
while driving on Booking A below).

## 4. System Setting (1)

| Key | Value |
|---|---|
| `rate_per_km` | `5.00` (NZD$ per km — matches `config.DEFAULT_RATE_PER_KM`) |

## 5. Bookings (3) — demonstrates all three vehicle-in-use statuses

**Booking A — CONFIRMED (future, upcoming pickup)**
- Customer: `customer_sita` · Vehicle: Hyundai Tucson (#2) · Driver: `driver_bikash`
- Pickup: 2026-09-20 · Return: 2026-09-23 (3 days) · Distance: 150 km
- Cost = (3 x $90) + (150 x $5) + (3 x $60) = $270 + $750 + $180 = **NZD$1,200.00**
- This is WHY vehicle #2 (Tucson) is seeded as BOOKED.

**Booking B — COMPLETED (past)**
- Customer: `customer_sita` · Vehicle: Toyota Corolla (#1) · No driver
- Pickup: 2026-08-01 · Return: 2026-08-03 (2 days) · Distance: 80 km
- Cost = (2 x $65) + (80 x $5) = $130 + $400 = **NZD$530.00**

**Booking C — ACTIVE (currently rented out)**
- Customer: `customer_gita` · Vehicle: Mahindra Scorpio (#10) · No driver
- Pickup: 2026-09-08 · Return: 2026-09-14 (6 days) · Distance: 300 km
- Cost = (6 x $88) + (300 x $5) = $528 + $1,500 = **NZD$2,028.00**
- This is WHY vehicle #10 (Scorpio) is seeded as RENTED.

## 6. Waitlist (1) — demonstrates the Smart Waitlist + Auto-Notify feature

- `customer_gita` tried to book the Hyundai Tucson (#2) for 2026-09-21 to
  2026-09-24 — overlaps Booking A, so it's rejected as unavailable, and she joins the
  waitlist for that vehicle instead (`notified = False`).
- **How to see it fire:** as admin, cancel or complete Booking A (or reject it before
  confirming) — the Tucson's status flips back to AVAILABLE, which should
  automatically notify `customer_gita` (console message / notification log entry).

## 7. Payments (3) — demonstrates all three payment statuses

| Booking | Amount (NZD$) | Method | Status |
|---|---|---|---|
| Booking A | 1,200.00 | CARD | PAID |
| Booking B | 530.00 | CASH | PAID |
| Booking C | 2,028.00 | BANK_TRANSFER | PARTIAL |

## 8. Total Seeded Records

6 users + 2 customer profiles + 3 vehicle-owner/driver profiles + 10 vehicles + 3
bookings + 1 waitlist entry + 3 payments + 1 setting = **29 rows** across 9 tables —
comfortably covers every menu and feature in the system with realistic, connected data
(not just random filler), so nothing needs to be manually created before a demo.
