"""
utils/author_decorator.py
==========================

WHAT THIS FILE IS FOR:
This module defines a custom Python DECORATOR called `author_info`. It is used to
"tag" the important classes in this project (for example RentalSystem, Admin,
Customer) with authorship metadata: the developer's name, student ID, and
institution. This is the same "Decorators" topic covered in the MSE-800 lecture
material (see Decorators.pptx / Decorator.py in the course notes) - here it is
applied to a real, practical use case: attaching authorship information directly
onto the code objects themselves, instead of only writing it in a comment.

WHY A DECORATOR (and not just a comment) - THE PYTHON CONCEPT BEING DEMONSTRATED:
A plain comment (# written by Anish) is only readable by a human looking at the
source file. A decorator, on the other hand, actually RUNS at import time and can
attach real attributes onto the class or function it decorates. That means the
authorship information becomes something the PROGRAM ITSELF can read and display
(for example, on the CLI "About" screen), not just something written in a comment
that Python ignores when it runs. This shows a decorator being used for a genuine
purpose: modifying/annotating an object automatically, without changing how the
class or function is written or called.

HOW A DECORATOR WORKS (recap):
- A decorator is a function that takes another function/class as its input and
  returns a (usually modified) function/class as its output.
- `author_info(name, student_id, institution)` below is a DECORATOR FACTORY: a
  function that itself returns a decorator, so that we can pass arguments
  (name, student_id, institution) into the decorator when we use it, like this:

      @author_info(name="Anish Shrestha", student_id="270889991")
      class RentalSystem:
          ...

WHERE IT IS USED IN THIS PROJECT:
Applied to key top-level classes (e.g. `RentalSystem` in services/rental_system.py,
added later) so that the "About Nepal Car Rental System" CLI screen can read
`RentalSystem.__author__`, `RentalSystem.__student_id__`, and
`RentalSystem.__institution__` directly from the class, proving the metadata is
genuinely wired into the running program rather than only appearing in text files.
"""

from functools import wraps


def author_info(name: str, student_id: str, institution: str = None):
    """
    Decorator factory that attaches authorship metadata to a class or a function.

    Arguments:
        name (str): The developer's full name.
        student_id (str): The developer's student ID number.
        institution (str, optional): The institution the work was produced for.

    Returns:
        A decorator function which, when applied to a class or function, attaches
        the metadata as attributes and returns the ORIGINAL class/function
        unchanged in every other way - so decorating something with @author_info
        never breaks how that class or function behaves.
    """

    def decorator(target):
        # Attach the metadata as attributes directly on the class/function object.
        # These follow Python's convention of "dunder" (double-underscore) names
        # for metadata, the same style Python itself uses for __name__, __doc__, etc.
        target.__author__ = name
        target.__student_id__ = student_id
        if institution:
            target.__institution__ = institution

        # If we are decorating a function (not a class), @wraps keeps the original
        # function's name and docstring intact, so debugging tools and help() still
        # show correct information about the real function, not about a wrapper.
        if not isinstance(target, type):
            @wraps(target)
            def wrapper(*args, **kwargs):
                return target(*args, **kwargs)
            wrapper.__author__ = name
            wrapper.__student_id__ = student_id
            if institution:
                wrapper.__institution__ = institution
            return wrapper

        # For a class, we can safely return the same class object with the new
        # attributes attached - no wrapping needed, because classes are not
        # "called" the way functions are.
        return target

    return decorator
