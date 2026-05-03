val p = ArraySequence.nth (ArraySequence.fromList [(0, 0), (0, 0)]) 0
val _ = ArraySequence.foreach (ArraySequence.singleton 0) (fn _ => (MLton.Trace.noTuple (#1 p); ()))
