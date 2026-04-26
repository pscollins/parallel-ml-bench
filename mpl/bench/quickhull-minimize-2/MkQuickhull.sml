functor MkQuickhull (Seq: SEQUENCE):
sig
  type 'a aseq = 'a ArraySequence.t
  val hull: (real * real) aseq -> int aseq
end =
struct

  structure AS = ArraySlice
  structure ASeq = ArraySequence
  type 'a aseq = 'a ASeq.t

  fun hull pts =
    let
      fun pt i = ASeq.nth pts i
      fun dist p q i =
          let
             val ((ax, ay), (bx, by), (cx, cy)) = (p, q, pt i)
             val ax' = MLton.Trace.noTuple ax
             val ay' = MLton.Trace.noTuple ay
             val bx' = MLton.Trace.noTuple bx
             val by' = MLton.Trace.noTuple by
             val cx' = MLton.Trace.noTuple cx
             val cy' = MLton.Trace.noTuple cy
             val x1 = bx' - ax'
             val y1 = by' - ay'
             val x2 = cx' - ax'
             val y2 = cy' - ay'
             val distResult = x1*y2 - y1*x2
             val _ = MLton.Trace.sourceMarkValue (distResult, "distResult")
          in
             distResult
          end

      datatype flag = Left | Right | Throwaway

      fun parSplit s flags =
        let
          fun countFlag i =
            case Seq.nth flags i of
              Left => (1, 0)
            | Right => (0, 1)
            | Throwaway => (0, 0)
          fun add ((a, b), (c, d)) = (a+c, b+d)
          val n = Seq.length s
          val (offsets, (tl, tr)) = Seq.scan add (0, 0) (Seq.tabulate countFlag n)
          val left = ForkJoin.alloc tl
          val right = ForkJoin.alloc tr
        in
          Seq.applyIdx offsets (fn (i, (offl, offr)) =>
            case Seq.nth flags i of
              Left => Array.update (left, offl, Seq.nth s i)
            | Right => Array.update (right, offr, Seq.nth s i)
            | _ => ()
          );
          (AS.full left, AS.full right)
        end

      fun parHull idxs l r =
        if ASeq.length idxs < 2 then
          ()
        else
          let
            val lp = pt l
            val rp = pt r
            val idxs_seq = Seq.fromArraySeq idxs
            val distances = Seq.map (fn i => (i, dist lp rp i)) idxs_seq
            val (mid, _) = Seq.reduce (fn ((i, di), (j, dj)) => if di > dj then (i, di) else (j, dj)) (~1, Real.negInf) distances
            val midp = pt mid
            fun flag i =
              if dist lp midp i > 0.0 then Left
              else if dist midp rp i > 0.0 then Right
              else Throwaway
            val (left, right) = parSplit idxs_seq (Seq.force (Seq.map flag idxs_seq))
            val _ = ForkJoin.par (fn _ => parHull left l mid, fn _ => parHull right mid r)
          in
            ()
          end

      val allIdx = Seq.tabulate (fn i => i) (ASeq.length pts)
      val (l, r) = Seq.reduce (fn ((l1, r1), (l2, r2)) => (if #1 (pt l1) < #1 (pt l2) then l1 else l2, if #1 (pt r1) > #1 (pt r2) then r1 else r2)) (0, 0) (Seq.map (fn i => (i, i)) allIdx)
      val lp = pt l
      val rp = pt r
      fun flag i =
        let val d = dist lp rp i
        in if d > 0.0 then Left else if d < 0.0 then Right else Throwaway
        end
      val (above, below) = parSplit allIdx (Seq.force (Seq.map flag allIdx))
      val _ = ForkJoin.par (fn _ => parHull above l r, fn _ => parHull below r l)
    in
      ASeq.fromList [0]
    end
end
