val a: real array = ForkJoin.alloc 1
val x = Array.sub (a, 0)
fun f n = if n = 0 then () else (MLton.Trace.noTuple x; ForkJoin.par (fn _ => f (n-1), fn _ => f (n-1)); ())
val _ = f 1
