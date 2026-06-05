functor MkQuickhull (Seq: SEQUENCE):
sig
  type 'a aseq = 'a ArraySequence.t
  val hull: (real * real) aseq -> int aseq
end =
struct

  structure AS = ArraySlice
  structure ASeq = ArraySequence
  type 'a aseq = 'a ASeq.t

  structure G = Geometry2D
  structure Tree = TreeSeq

  structure Split = MkSplit (Seq)

  fun hull pts =
    let
      fun pt i = ASeq.nth pts i
      fun triArea ((ax, ay), (bx, by), (cx, cy)) =
          let
             val x1 = bx - ax
             val y1 = by - ay
             val x2 = cx - ax
             val y2 = cy - ay
             val result = x1*y2 - y1*x2
          in
             result
          end

      fun dist pts p q i = let
         val distResult = triArea (p, q, ASeq.nth pts i)
         (* val _ = MLton.Trace.sourceMarkValue (distResult, "distResult") *)
      in
         distResult
      end
      fun max ((i, di), (j, dj)) =
        if di > dj then (i, di) else (j, dj)
      fun x i = #1 (pt i)

      fun aboveLine pts p q i = (dist pts p q i > 0.0)

      fun parHull pts idxs l r =
        if ASeq.length idxs < 2 then
          Tree.fromArraySeq idxs
        else
          let
            val lp = ASeq.nth pts l
            val rp = ASeq.nth pts r
            fun dist' pts l r i = let
               val p = ASeq.nth pts l
               val q = ASeq.nth pts r
               val distResult = triArea (p, q, ASeq.nth pts i)
               (* val _ = MLton.Trace.sourceMarkValue (distResult, "distResult2") *)
            in
               distResult
            end
            fun d i = dist' pts l r i

            val idxs = Seq.fromArraySeq idxs

            val distances = Seq.map (fn i => (i, d i)) idxs
            val (mid, _) = Seq.reduce max (~1, Real.negInf) distances

            val midp = ASeq.nth pts mid

            fun flag pts i =
              if aboveLine pts lp midp i then Split.Left
              else if aboveLine pts midp rp i then Split.Right
              else Split.Throwaway
            val (left, right) =
              Split.parSplit idxs (Seq.force (Seq.map (flag pts) idxs))

            fun doLeft () = parHull pts left l mid
            fun doRight () = parHull pts right mid r
            val (leftHull, rightHull) =
              if ASeq.length left + ASeq.length right <= 2048
              then (doLeft (), doRight ())
              else ForkJoin.par (doLeft, doRight)
          in
            Tree.append (leftHull,
                         (Tree.append (Tree.$ mid, rightHull)))
          end

      (* val tm = Util.startTiming () *)

      val len = ASeq.length pts
      val allIdx = Seq.tabulate (fn i => i) (len)

      (* This is faster than doing two reduces *)
      val (l, r) = Seq.reduce
        (fn ((l1, r1), (l2, r2)) =>
          (if x l1 < x l2 then l1 else l2,
           if x r1 > x r2 then r1 else r2))
        (0, 0)
        (Seq.map (fn i => (i, i)) allIdx)

      (* val tm = Util.tick tm "endpoints" *)

      val lp = pt l
      val rp = pt r

      fun flag pts i =
        let
          val d = dist pts lp rp i
        in
          if d > 0.0 then Split.Left
          else if d < 0.0 then Split.Right
          else Split.Throwaway
        end
      val (above, below) =
        Split.parSplit allIdx (Seq.force (Seq.map (flag pts) allIdx))

      (* val tm = Util.tick tm "above/below filter" *)

      val (above, below) = ForkJoin.par
        (fn _ => parHull pts above l r,
         fn _ => parHull pts below r l)

      (* val tm = Util.tick tm "quickhull" *)

      val hullt =
        Tree.append
          (Tree.append (Tree.$ l, above),
           Tree.append (Tree.$ r, below))

      val result = Tree.toArraySeq hullt

      (* val tm = Util.tick tm "flatten" *)
    in
      result
    end

end
