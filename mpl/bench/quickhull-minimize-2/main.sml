structure Seq = ArraySequence
structure Quickhull = MkQuickhull(OldDelayedSeq)

val n = 100
val inputPts = Seq.tabulate (fn i => (Real.fromInt i, Real.fromInt i)) n

val result = Quickhull.hull inputPts
val _ = print ("hull size " ^ Int.toString (Seq.length result) ^ "\n")
