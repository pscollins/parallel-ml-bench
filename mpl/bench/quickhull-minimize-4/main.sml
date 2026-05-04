(* val xs: (Int32.int * Int32.int) ArraySequence.t = ArraySequence.fromList [(0, 0), (0, 0)] *)
val xs: (Int64.int * Int64.int) ArraySequence.t = ArraySequence.fromList [(0, 0), (0, 0)]
val p = ArraySequence.nth xs 0
(* val _ = ArraySequence.foreach (ArraySequence.singleton 0) (fn _ => (MLton.Trace.noTuple (#1 p); ())) *)
val _ = ArraySequence.foreach (ArraySequence.singleton 0) (fn _ => (MLton.Trace.sourceMarkValue (#1 p, "coord1"); ()))
