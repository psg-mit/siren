open Ztypes
open Probzelus

let prob = ref (Obj.magic ())

let sample =
  let (Cnode { alloc; reset; copy; step }) = Infer_semi_symbolic.sample in
  let step self (_, x) = step self (!prob, x) in
  Cnode { alloc; reset; copy; step }

let observe =
  let (Cnode { alloc; reset; copy; step }) = Infer_semi_symbolic.observe in
  let step self (_, x) = step self (!prob, x) in
  Cnode { alloc; reset; copy; step }

let infer n f =
  let (Cnode { alloc; reset; copy; step }) = f in
  let step self (proba, x) =
    prob := proba;
    step self (!prob, x)
  in
  let f = Cnode { alloc; reset; copy; step } in
  Infer_semi_symbolic.infer_marginal n f

let ite (i, t, e) = Infer_semi_symbolic.ite i t e

let lt_det (a, b) = a < b

let eq_det (a, b) = a = b

let add_int (x, y) = x + y

let sub_int (x, y) = x - y

let add_float (x, y) = x +. y

let sub_float (x, y) = x -. y

let pow (x, y) = x ** y

let exit code = exit(code)

let concat(a, b) = a ^ b

let exact (x) = 
  Format.print_string "exact ";
  Format.print_newline ();
  x

let approx (x) =
  Infer_semi_symbolic.const(Infer_semi_symbolic.eval x)
  (* Format.print_string "approx ";
  Format.print_newline (); 
  x *)

let read file = 
  let data = ref [] in
  let ic = open_in file in
  let first = ref true in
  try
    while true; do
      let line = input_line ic in
      if !first then
        first := false
      else begin
        let line_list = String.split_on_char ',' line in
        let line_list = List.map int_of_string line_list in
        data := line_list :: !data
      end
    done;
    !data
  with 
  | End_of_file -> close_in ic; !data
  | e ->
    close_in_noerr ic;
    raise e

let random_order len =
  let sample_fn _ =
    let arr = Array.init len (fun i -> i) in
    for n = Array.length arr - 1 downto 1 do
      let k = Random.int (n + 1) in
      let tmp = arr.(n) in
      arr.(n) <- arr.(k);
      arr.(k) <- tmp
    done;
    arr
  in

  let obs_fn _ = assert false in

  Infer_semi_symbolic.of_distribution (Types.Dist_sampler(sample_fn, obs_fn))


module List = struct
  let length l = List.length l

  let nil = []

  let nil2 = []

  let hd = List.hd

  let tl = List.tl

  let cons (x, l) = x :: l

  let filter (f, l) = List.filter f l

  let init (n, f) = List.init n f

  let append (a, b) = List.append a b

  let map (f, l) = List.map f l

  let iter (f, l) = List.iter f l

  let fold (f, a, b) = List.fold_left (fun a b -> f (a, b)) a b

  let zip (a, b) = List.map2 (fun x y -> (x, y)) a b

  let iter2 (f, l1, l2) =
    let f a b = f (a, b) in
    List.iter2 f l1 l2

  let shuffle (order, l) = 
    let l_arr = Array.of_list l in
    let new_arr = Array.init (Array.length l_arr) (fun i -> Array.get l_arr (Array.get order i)) in
    Array.to_list new_arr
end

module Array = struct
  let empty = [||]

  let init (n, f) = Array.init n f

  let get (a, x) = Array.get a x
end
