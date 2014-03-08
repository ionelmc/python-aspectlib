Changelog
=========

Version 0.4.0
-------------

* Changed :obj:`aspectlib.weave`:

    * Replaced `only_methods`, `skip_methods`, `skip_magicmethods` options with `methods`.
    * Renamed `on_init` option to `lazy`.
    * Added `aliases` option.
    * Replaced `skip_subclasses` option with `subclasses`.

* Fixed weaving methods from a string target.
