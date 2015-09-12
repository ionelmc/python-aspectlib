Rationale
=========

There are perfectly sane use cases for monkey-patching (aka *weaving*):

* Instrumenting existing code for debugging, profiling and other measurements.
* Testing less flexible code. In some situations it's infeasible to use dependency injection to make your code more
  testable.

Then in those situations:

* You would need to handle yourself all different kinds of patching (patching
  a module is different than patching a class, a function or a method for that matter).
  ``aspectlib`` will handle all this gross patching mumbo-jumbo for you, consistently, over many Python versions.
* Writing the actual wrappers is repetitive, boring and error-prone. You can't reuse wrappers
  but *you can reuse function decorators*.
