functor MkPurishSplit (Seq: SEQUENCE) :
sig
  type 'a seq = 'a Seq.t
  type 'a aseq = 'a PlainArraySequence.t

  datatype flag = Left | Right | Throwaway
  val parSplit: 'a seq -> flag seq -> 'a aseq * 'a aseq
end =
struct

  structure A = Array
  structure AS = ArraySlice
  structure ASeq = PlainArraySequence

  type 'a seq = 'a Seq.t
  type 'a aseq = 'a ASeq.t

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

      (left, right)
      end
end
