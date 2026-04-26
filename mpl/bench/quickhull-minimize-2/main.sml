functor MkQuickhull (Seq: SEQUENCE) =
struct
  structure ASeq = ArraySequence

  fun hull (pts: (real * real) ASeq.t) =
    let
      fun pt i = ASeq.nth pts i
      fun dist p i =
          let
             val (ax, ay) = p
             val ax' = MLton.Trace.noTuple ax
             val ay' = MLton.Trace.noTuple ay
          in
             ax' + ay'
          end

      fun parHull idxs_seq n =
        if n <= 0 then ()
        else
          let
            val p0 = pt 0
            val _ = Seq.force (Seq.map (fn i => dist p0 i) idxs_seq)
            val _ = ForkJoin.par (fn _ => parHull idxs_seq (n-1), fn _ => parHull idxs_seq (n-1))
          in
            ()
          end

      val allIdx = Seq.tabulate (fn i => i) (ASeq.length pts)
      val _ = parHull allIdx 1
    in
      ASeq.fromList [0]
    end
end

structure Quickhull = MkQuickhull(OldDelayedSeq)

structure Seq = ArraySequence
val n = 100
val inputPts = Seq.tabulate (fn i => (Real.fromInt i, Real.fromInt i)) n
val result = Quickhull.hull inputPts
val _ = print ("hull size " ^ Int.toString (Seq.length result) ^ "\n")
