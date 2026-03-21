structure TreeSeq =
struct
  datatype 'a t = Leaf | Node of 'a t * 'a t
  fun length _ = 0
  fun append (t1, t2) = Node (t1, t2)
  fun toArraySeq _ = ArraySlice.full (Array.fromList [])
  fun fromArraySeq _ = Leaf
  fun singleton _ = Leaf
  val $ = singleton
end
