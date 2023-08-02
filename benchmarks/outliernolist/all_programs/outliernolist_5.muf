val preprocess_data = fun entry -> List.hd(List.tl(entry)) in

val step = fun (prev, yobs) ->
  let (first, prev) = split(prev) in
  let (outlier_prob, prev_xt) = split(prev) in

  let xt_mu = if first then 0. else prev_xt in
  let xt_var = if first then 2500. else 1. in

  let approx xt <- gaussian(xt_mu, xt_var) in
  let exact is_outlier <- bernoulli(outlier_prob) in
  let mu = if is_outlier then 0. else xt in
  let var = if is_outlier then 10000. else 1. in
  let () = observe(gaussian(mu, var), yobs) in
  
  (false, outlier_prob, xt)
in

val output = fun out ->
  let (outlier_prob, x) = split(out) in
  let () = Print.print_float (mean_float(outlier_prob)) in
  let () = Print.print_endline () in
  let () = Print.print_float (mean_float(x)) in
  ()
in


(* observations *)
let data = List.map(preprocess_data, read("data/processed_data.csv")) in

let approx outlier_prob <- beta(100., 1000.) in
let (_, res) = split(List.fold_resample(step, data, (true, outlier_prob, 0.))) in
let (outlier_prob, x) = split(res) in

(outlier_prob, x)
