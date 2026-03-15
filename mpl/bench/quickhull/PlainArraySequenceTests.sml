structure PlainArraySequenceTests =
struct
  structure S = PlainArraySequence

  fun assert cond msg =
    if cond then () else raise Fail ("Assertion failed: " ^ msg)

  fun testAll () =
    let
      val _ = print "Testing PlainArraySequence...\n"
      
      val a = S.fromList [1, 2, 3, 4, 5]
      val _ = assert (S.length a = 5) "length"
      val _ = assert (S.nth a 0 = 1) "nth 0"
      val _ = assert (S.nth a 4 = 5) "nth 4"

      val b = S.tabulate (fn i => i * 2) 3
      val _ = assert (S.length b = 3) "tabulate length"
      val _ = assert (S.nth b 0 = 0) "tabulate 0"
      val _ = assert (S.nth b 1 = 2) "tabulate 1"
      val _ = assert (S.nth b 2 = 4) "tabulate 2"

      val c = S.map (fn x => x + 1) a
      val _ = assert (S.nth c 0 = 2) "map 0"
      val _ = assert (S.nth c 4 = 6) "map 4"

      val d = S.subseq a (1, 3)
      val _ = assert (S.length d = 3) "subseq length"
      val _ = assert (S.nth d 0 = 2) "subseq 0"
      val _ = assert (S.nth d 2 = 4) "subseq 2"

      val e = S.append (b, d)
      val _ = assert (S.length e = 6) "append length"
      val _ = assert (S.nth e 0 = 0) "append 0"
      val _ = assert (S.nth e 3 = 2) "append 3"

      val (sum_prefixes, total) = S.scan (op +) 0 a
      val _ = assert (total = 15) "scan total"
      val _ = assert (S.nth sum_prefixes 0 = 0) "scan prefix 0"
      val _ = assert (S.nth sum_prefixes 4 = 10) "scan prefix 4"

      val sum_incl = S.scanIncl (op +) 0 a
      val _ = assert (S.nth sum_incl 0 = 1) "scanIncl 0"
      val _ = assert (S.nth sum_incl 4 = 15) "scanIncl 4"

      val f = S.filter (fn x => x mod 2 = 0) a
      val _ = assert (S.length f = 2) "filter length"
      val _ = assert (S.nth f 0 = 2) "filter 0"
      val _ = assert (S.nth f 1 = 4) "filter 1"

      val _ = print "All tests passed!\n"
    in
      ()
    end
end

val _ = PlainArraySequenceTests.testAll ()
