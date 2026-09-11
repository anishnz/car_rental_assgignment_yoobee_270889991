"""
models/observer.py
===================

WHAT THIS FILE IS FOR:
Defines the Observer "interface" used by the Smart Waitlist + Auto-Notify feature -
the project's innovative feature (see docs/01_requirements_analysis.md section 9).

WHAT THE OBSERVER DESIGN PATTERN IS AND WHY WE USE IT:
The Observer pattern describes a one-to-many relationship: one "Subject" object (here,
a Vehicle) can have many "Observer" objects watching it (here, the customers waiting
for that vehicle). When something the observers care about happens to the subject -
the vehicle becoming AVAILABLE again - the subject tells every observer about it,
without the subject needing to know anything about WHAT each observer will do with
that information. This keeps the code loosely coupled: Vehicle only needs to know
"call on_vehicle_available() on each of my observers", not "customer_gita cares about
this vehicle, so print a message mentioning her by name".

HOW PYTHON EXPRESSES AN "INTERFACE":
Python does not have a separate `interface` keyword like Java or C#. Instead, we use
the `abc` (Abstract Base Class) module from the standard library: a class that
inherits from `ABC` and marks a method with `@abstractmethod` CANNOT be instantiated
directly, and any subclass MUST override that method or Python will raise an error
when trying to create it. This is exactly the guarantee a real interface gives us.
"""

from abc import ABC, abstractmethod


class Observer(ABC):
    """Anything that wants to be notified when a vehicle becomes available again
    must inherit from this class and implement on_vehicle_available()."""

    @abstractmethod
    def on_vehicle_available(self, vehicle):
        """
        Called by the Subject (a Vehicle) when it becomes AVAILABLE again.
        `vehicle` is the Vehicle instance that just freed up.
        """
        raise NotImplementedError
