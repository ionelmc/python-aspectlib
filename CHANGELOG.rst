Changelog
=========

1.4.1 (2016-05-06)
------------------

* Fixed weaving of objects that don't live on root-level modules.

1.4.0 (2016-04-09)
------------------

* Corrected weaving of methods, the weaved function should be unbound.
* Rolling back only applies undos once.
* Added a convenience `weave` fixture for pytest.

1.3.3 (2015-10-02)
------------------

* Fixed typo in ``ABSOLUTELLY_ALL_METHODS`` name (now ``ABSOLUTELY_ALL_METHODS``). Old name is still there for
  backwards compatibility.

1.3.2 (2015-09-22)
------------------

* Fixed another tricky bug in the generator advising wrappers - result was not returned if only `Proceed` was yielded.

1.3.1 (2015-09-12)
------------------

* Corrected result handling when using Aspects on generators.

1.3.0 (2015-06-06)
------------------

* Added ``messages`` property to :obj:`aspectlib.test.LogCapture`. Change ``call`` to have level name instead of number.
* Fixed a bogus warning from :func:`aspectlib.patch_module`` when patching methods on old style classes.

1.2.2 (2014-11-25)
------------------

* Added support for weakrefs in the ``__logged__`` wrapper from :obj:`aspectlib.debug.log` decorator.

1.2.1 (2014-10-15)
------------------

* Don't raise exceptions from ``Replay.__exit__`` if there would be an error (makes original cause hard to debug).

1.2.0 (2014-06-24)
------------------

* Fixed weaving methods that were defined in some baseclass (and not on the target class).
* Fixed wrong qualname beeing used in the Story/Replay recording. Now used the alias given to the weaver instead of
  whatever is the realname on the current platform.

1.1.1 (2014-06-14)
------------------

* Use ``ASPECTLIB_DEBUG`` for every logger in ``aspectlib``.

1.1.0 (2014-06-13)
------------------

* Added a `bind` option to :obj:`aspectlib.Aspect` so you can access the cutpoint from the advisor.
* Replaced automatic importing in :obj:`aspectlib.test.Replay` with extraction of context variables (locals and globals
  from the calling :obj:`aspectlib.test.Story`). Works better than the previous inference of module from AST of the
  result.
* All the methods on the replay are now properties: :obj:`aspectlib.test.Story.diff`,
  :obj:`aspectlib.test.Story.unexpected` and :obj:`aspectlib.test.Story.missing`.
* Added :obj:`aspectlib.test.Story.actual` and :obj:`aspectlib.test.Story.expected`.
* Added an ``ASPECTLIB_DEBUG`` environment variable option to switch on debug logging in ``aspectlib``'s internals.

1.0.0 (2014-05-03)
------------------

* Reworked the internals :obj:`aspectlib.test.Story` to keep call ordering, to allow dependencies and improved the
  serialization (used in the diffs and the missing/unexpected lists).


0.9.0 (2014-04-16)
------------------

* Changed :obj:`aspectlib.test.record`:

    * Renamed `history` option to `calls`.
    * Renamed `call` option to `iscalled`.
    * Added `callback` option.
    * Added `extended` option.

* Changed :obj:`aspectlib.weave`:

    * Allow weaving everything in a module.
    * Allow weaving instances of new-style classes.

* Added :obj:`aspectlib.test.Story` class for capture-replay and stub/mock testing.

0.8.1 (2014-04-01)
------------------

* Use simpler import for the py3support.

0.8.0 (2014-03-31)
------------------

* Change :obj:`aspectlib.debug.log` to use :obj:`~aspectlib.Aspect` and work as expected with coroutines or generators.
* Fixed :obj:`aspectlib.debug.log` to work on Python 3.4.
* Remove the undocumented ``aspectlib.Yield`` advice. It was only usable when decorating generators.

0.7.0 (2014-03-28)
------------------

* Add support for decorating generators and coroutines in :obj:`~aspectlib.Aspect`.
* Made aspectlib raise better exceptions.

0.6.1 (2014-03-22)
------------------

* Fix checks inside :obj:`aspectlib.debug.log` that would inadvertently call ``__bool__``/``__nonzero``.

0.6.0 (2014-03-17)
------------------

* Don't include __getattribute__ in ALL_METHODS - it's too dangerous dangerous dangerous dangerous dangerous dangerous
  ... ;)
* Do a more reliable check for old-style classes in debug.log
* When weaving a class don't weave attributes that are callable but are not actually routines (functions, methods etc)

0.5.0 (2014-03-16)
------------------

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

0.4.1 (2014-03-08)
------------------

* Remove junk from 0.4.0's source distribution.

0.4.0 (2014-03-08)
------------------

* Changed :obj:`aspectlib.weave`:

    * Replaced `only_methods`, `skip_methods`, `skip_magicmethods` options with `methods`.
    * Renamed `on_init` option to `lazy`.
    * Added `aliases` option.
    * Replaced `skip_subclasses` option with `subclasses`.

* Fixed weaving methods from a string target.

0.3.1 (2014-03-05)
------------------

* ???

0.3.0 (2014-03-05)
------------------

* First public release.
