structure Seq = OldDelayedSeq

val a = Array.fromList [0.0, 0.1]
val lp = Array.sub (a, 0)
val flags = Seq.map (fn x =>
    let val ax' = MLton.Trace.noTuple lp
    in ax' + x
    end) (Seq.fromArraySeq (ArraySlice.full a))
val _ = Seq.scan (fn (a, b) => a + b) 0.0 flags
