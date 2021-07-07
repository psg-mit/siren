open Ztypes
open Probzelus

let prob = ref (Obj.magic())

let sample =
  let Cnode { alloc; reset; copy; step; } = Infer_ds_streaming.sample in
  let step self (_, x) = step self (!prob, x) in
  Cnode { alloc; reset; copy; step; }

let observe =
  let Cnode { alloc; reset; copy; step; } = Infer_ds_streaming.observe in
  let step self (_, x) = step self (!prob, x) in
  Cnode { alloc; reset; copy; step; }

let infer n f =
  let Cnode { alloc; reset; copy; step; } = f in
  let step self (proba, x) =
    prob := proba;
    step self (!prob, x)
  in
  let f = Cnode { alloc; reset; copy; step; } in
  Infer_ds_streaming.infer n f

let ite (i, t, e)  = Infer_ds_streaming.ite i t e

let add_int (x, y) = x + y

module Array = struct
  let empty = Array.make 100 (Infer_ds_streaming.const false)

  let init (n, f) = Array.init n f 

  let get (a, x) = Array.get a x

end