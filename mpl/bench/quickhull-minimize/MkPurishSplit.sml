functor MkPurishSplit (Seq: SEQUENCE) :
sig
  datatype flag = Left | Right | Throwaway
  val parSplit: 'a Seq.t -> flag Seq.t -> 'a ArraySequence.t * 'a ArraySequence.t
end =
struct
  datatype flag = Left | Right | Throwaway
  fun parSplit s flags = (ArraySlice.full (Array.fromList []), ArraySlice.full (Array.fromList []))
end
