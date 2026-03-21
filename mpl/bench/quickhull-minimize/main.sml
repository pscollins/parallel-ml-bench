structure Seq = ArraySequence
structure Quickhull = MkQuickhull(OldDelayedSeq)
val pts = Seq.tabulate (fn _ => (0.0, 0.0)) 1
val _ = Quickhull.hull pts
