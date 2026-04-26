Notes from minimization process with Gemini:

✦ I have successfully reduced the reproducer for the compiler bug from over 1,000 bytes down to just two essential lines in main.sml. The minimal code that triggers the Found forbidden tuple
  operations error is:

   1 val p0 = MLton.Trace.noTuple (0, 0)
   2 val _ = ArraySequence.tabulate (fn _ => MLton.Trace.noTuple (#1 p0)) 1

  Through iterative testing and simplification, I discovered several key requirements for reproducing this bug:
   1. Initial Tuple Creation: A tuple must be created through an "uncertain" source that the compiler cannot easily optimize away. Using MLton.Trace.noTuple (0, 0) is the most direct way to
      achieve this.
   2. Closure Capture: This tuple must be captured in the closure of a parallel or sequence operation (like ArraySequence.tabulate). Simple capture in ForkJoin.par or a regular function was
      insufficient.

