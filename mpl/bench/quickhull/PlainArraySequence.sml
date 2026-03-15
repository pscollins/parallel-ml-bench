signature SEQUENCE =
sig
  type 'a t
  type 'a seq = 'a t
  val nth: 'a seq -> int -> 'a
  val length: 'a seq -> int
  val tabulate: (int -> 'a) -> int -> 'a seq
  val map: ('a -> 'b) -> 'a seq -> 'b seq
  val mapIdx: (int * 'a -> 'b) -> 'a seq -> 'b seq
  val subseq: 'a seq -> int * int -> 'a seq
  val take: 'a seq -> int -> 'a seq
  val drop: 'a seq -> int -> 'a seq
  val fromList: 'a list -> 'a seq
  val toList: 'a seq -> 'a list
  val toString: ('a -> string) -> 'a seq -> string
  val empty: unit -> 'a seq
  val singleton: 'a -> 'a seq
  val $ : 'a -> 'a seq
  val % : 'a list -> 'a seq
  val append: 'a seq * 'a seq -> 'a seq
  val foreach: 'a seq -> (int * 'a -> unit) -> unit
  val reduce: ('a * 'a -> 'a) -> 'a -> 'a seq -> 'a
  val scan: ('a * 'a -> 'a) -> 'a -> 'a seq -> 'a seq * 'a
  val scanIncl: ('a * 'a -> 'a) -> 'a -> 'a seq -> 'a seq
  val fromArraySeq: 'a ArraySlice.slice -> 'a seq
  val toArraySeq: 'a seq -> 'a ArraySlice.slice
  val force: 'a seq -> 'a seq
  val zip: 'a seq * 'b seq -> ('a * 'b) seq
  val zipWith: ('a * 'b -> 'c) -> 'a seq * 'b seq -> 'c seq
  val filter: ('a -> bool) -> 'a seq -> 'a seq
  val applyIdx: 'a seq -> (int * 'a -> unit) -> unit
end

structure PlainArraySequence : SEQUENCE =
struct
  type 'a t = 'a array
  type 'a seq = 'a t

  fun length a = Array.length a
  fun nth a i = Array.sub (a, i)

  fun tabulate f n = Array.tabulate (n, f)

  fun map f a = 
    let
      val n = Array.length a
    in
      if n = 0 then Array.fromList []
      else
        let
          val first = f (Array.sub (a, 0))
          val res = Array.array (n, first)
          fun loop i =
            if i >= n then ()
            else (Array.update (res, i, f (Array.sub (a, i))); loop (i + 1))
        in
          loop 1;
          res
        end
    end

  fun mapIdx f a =
    let
      val n = Array.length a
    in
      if n = 0 then Array.fromList []
      else
        let
          val first = f (0, Array.sub (a, 0))
          val res = Array.array (n, first)
          fun loop i =
            if i >= n then ()
            else (Array.update (res, i, f (i, Array.sub (a, i))); loop (i + 1))
        in
          loop 1;
          res
        end
    end

  fun subseq a (i, len) =
    Array.tabulate (len, fn j => Array.sub (a, i + j))

  fun take a n = subseq a (0, n)
  fun drop a n = subseq a (n, Array.length a - n)

  fun fromList l = Array.fromList l
  fun toList a = Array.foldr (fn (x, acc) => x :: acc) [] a

  fun toString f a =
    "<" ^ String.concatWith "," (List.map f (toList a)) ^ ">"

  fun empty () = Array.fromList []
  fun singleton x = Array.array (1, x)
  val $ = singleton
  fun % l = Array.fromList l

  fun append (a, b) =
    let
      val na = Array.length a
      val nb = Array.length b
    in
      tabulate (fn i => if i < na then Array.sub (a, i) else Array.sub (b, i - na)) (na + nb)
    end

  fun foreach a f =
    let
      val n = Array.length a
      fun loop i =
        if i >= n then ()
        else (f (i, Array.sub (a, i)); loop (i + 1))
    in
      loop 0
    end

  fun reduce f b a =
    Array.foldl f b a

  fun scan f b a =
    let
      val n = Array.length a
      val res = Array.array (n, b)
      fun loop i cur =
        if i >= n then cur
        else
          let
            val _ = Array.update (res, i, cur)
          in
            loop (i + 1) (f (cur, Array.sub (a, i)))
          end
      val total = loop 0 b
    in
      (res, total)
    end

  fun scanIncl f b a =
    let
      val (s, t) = scan f b a
      val n = Array.length a
      val res = Array.array (n, b)
    in
      if n = 0 then Array.fromList []
      else
        let
          fun loop i =
            if i >= n - 1 then 
              (Array.update(res, i, t); ())
            else
              (Array.update(res, i, Array.sub(s, i+1)); loop (i+1))
        in
          loop 0;
          res
        end
    end

  fun fromArraySeq (slice: 'a ArraySlice.slice) =
    let
      val (base, start, len) = ArraySlice.base slice
    in
      Array.tabulate (len, fn i => Array.sub (base, start + i))
    end

  fun toArraySeq a = ArraySlice.full a

  fun force a = a

  fun applyIdx a f = foreach a f

  fun zip (a, b) =
    let
      val n = Int.min (Array.length a, Array.length b)
    in
      tabulate (fn i => (Array.sub (a, i), Array.sub (b, i))) n
    end

  fun zipWith f (a, b) =
    let
      val n = Int.min (Array.length a, Array.length b)
    in
      tabulate (fn i => f (Array.sub (a, i), Array.sub (b, i))) n
    end

  fun filter p a =
    let
      val l = Array.foldr (fn (x, acc) => if p x then x :: acc else acc) [] a
    in
      Array.fromList l
    end
end
