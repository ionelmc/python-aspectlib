Changelog
=========

Version 1.2.0
-------------

* Fix weaving methods that were defined in some baseclass (and not on the target class).
* Fix wrong qualname beeing used in the Story/Replay recording. Now used the alias given to the weaver instead of
  whatever is the realname on the current platform.

Version 1.1.1
-------------

* Use ``ASPECTLIB_DEBUG`` for every logger in ``aspectlib``.

Version 1.1.0
-------------

* Add a `bind` option to :obj:`aspectlib.Aspect` so you can access the cutpoint from the advisor.
* Replaced automatic importing in :obj:`aspectlib.test.Replay` with extraction of context variables (locals and globals
  from the calling :obj:`aspectlib.test.Story`). Works better than the previous inference of module from AST of the
  result.
* All the methods on the replay are now properties: :obj:`aspectlib.test.Story.diff`,
  :obj:`aspectlib.test.Story.unexpected` and :obj:`aspectlib.test.Story.missing`.
* Added :obj:`aspectlib.test.Story.actual` and :obj:`aspectlib.test.Story.expected`.
* Added an ``ASPECTLIB_DEBUG`` environment variable option to switch on debug logging in ``aspectlib``'s internals.

Version 1.0.0
-------------

* Reworked the internals :obj:`aspectlib.test.Story` to keep call ordering, to allow dependencies and improved the
  serialization (used in the diffs and the missing/unexpected lists).


Version 0.9.0
-------------

* Changed :obj:`aspectlib.test.record`:

    * Renamed `history` option to `calls`.
    * Renamed `call` option to `iscalled`.
    * Added `callback` option.
    * Added `extended` option.

* Changed :obj:`aspectlib.weave`:

    * Allow weaving everything in a module.
    * Allow weaving instances of new-style classes.

* Added :obj:`aspectlib.test.Story` class for capture-replay and stub/mock testing.

Version 0.8.1
-------------

* Use simpler import for the py3support.

Version 0.8.0
-------------

* Change :obj:`aspectlib.debug.log` to use :obj:`~aspectlib.Aspect` and work as expected with coroutines or generators.
* Fixed :obj:`aspectlib.debug.log` to work on Python 3.4.
* Remove the undocumented ``aspectlib.Yield`` advice. It was only usable when decorating generators.

Version 0.7.0
-------------

* Add support for decorating generators and coroutines in :obj:`~aspectlib.Aspect`.
* Made aspectlib raise better exceptions.

Version 0.6.1
-------------

* Fix checks inside :obj:`aspectlib.debug.log` that would inadvertently call ``__bool__``/``__nonzero``.

Version 0.6.0
-------------

* Don't include __getattribute__ in ALL_METHODS - it's too dangerous dangerous dangerous dangerous dangerous dangerous
  ... ;)
* Do a more reliable check for old-style classes in debug.log
* When weaving a class don't weave attributes that are callable but are not actually routines (functions, methods etc)

Version 0.5.0
-------------

* Changed :obj:`aspectlib.debug.log`:

    * Renamed `arguments` to `call_args`.
    * Renamed `arguments_repr` to `call_args_repr`.
    * Added `call` option.
    * Fixed issue with logging from old-style methods (object name was a generic "instance").

* Fixed issues with weaving some types of builtin methods.
* Allow to apply multiple aspects at the same time.
* Validate string targets before weaving. ``aspectlib.weave('mod.invalid name', aspect)`` now gives a clear error
  (``invalid name`` is not a valid identifier)
* Various documentation improvements and examples.

Version 0.4.1
-------------

* Remove junk from 0.4.0's source distribution.

Version 0.4.0
-------------

* Changed :obj:`aspectlib.weave`:

    * Replaced `only_methods`, `skip_methods`, `skip_magicmethods` options with `methods`.
    * Renamed `on_init` option to `lazy`.
    * Added `aliases` option.
    * Replaced `skip_subclasses` option with `subclasses`.

* Fixed weaving methods from a string target.
