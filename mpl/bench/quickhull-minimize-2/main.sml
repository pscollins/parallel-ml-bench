structure AS = ArraySequence

fun hull pts =
  let
    val p0 = AS.nth pts 0
    val _ = AS.tabulate (fn i => (MLton.Trace.noTuple (#1 p0); MLton.Trace.noTuple (#2 p0))) 1
  in
    ()
  end

val _ = hull (AS.tabulate (fn i => (0.0, 0.0)) 1)
