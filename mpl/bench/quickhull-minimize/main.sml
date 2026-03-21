val x = Array.sub (ForkJoin.alloc 1: real array, 0)
fun f n = if n = 0 then () else (MLton.Trace.noTuple x; ForkJoin.par (fn _ => f (n-1), fn _ => ()); ())
val _ = f 1
