functor MkQuickhull (Seq: SEQUENCE):
sig
  type 'a aseq = 'a ArraySequence.t
  val hull: (real * real) aseq -> int aseq
end =
struct

  structure ASeq = ArraySequence
  type 'a aseq = 'a ASeq.t
  structure Tree = TreeSeq
  structure Split = MkSplit (Seq)

  fun hull pts =
    let
      fun pt i = ASeq.nth pts i
      fun triArea ((ax, ay), (bx, by), (cx, cy)) =
          let
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
          in
             x1*y2 - y1*x2
          end

      fun parHull idxs l r =
        if ASeq.length idxs < 2 then
          Tree.fromArraySeq idxs
        else
          let
            val lp = pt l
            val rp = pt r
            val idxsSeq = Seq.fromArraySeq idxs
            val distances = Seq.map (fn i => (i, triArea (lp, rp, pt i))) idxsSeq
            val (mid, _) = Seq.reduce (fn ((i, di), (j, dj)) => if di > dj then (i, di) else (j, dj)) (~1, Real.negInf) distances
            val midp = pt mid
            fun flag i =
              if triArea (lp, midp, pt i) > 0.0 then Split.Left
              else if triArea (midp, rp, pt i) > 0.0 then Split.Right
              else Split.Throwaway
            val (left, right) =
              Split.parSplit idxsSeq (Seq.force (Seq.map flag idxsSeq))
          in
            Tree.append (parHull left l mid,
                         (Tree.append (Tree.$ mid, parHull right mid r)))
          end

      val allIdx = Seq.tabulate (fn i => i) (ASeq.length pts)
      val l = 0
      val r = 0
      val lp = pt l
      val rp = pt r

      fun flag i =
        let val d = triArea (lp, rp, pt i)
        in if d > 0.0 then Split.Left
           else if d < 0.0 then Split.Right
           else Split.Throwaway
        end
      val (above, below) =
        Split.parSplit allIdx (Seq.force (Seq.map flag allIdx))

      val (above, below) = ForkJoin.par
        (fn _ => parHull above l r,
         fn _ => parHull below r l)

      val hullt = Tree.append (Tree.append (Tree.$ l, above), Tree.append (Tree.$ r, below))
    in
      Tree.toArraySeq hullt
    end
end
