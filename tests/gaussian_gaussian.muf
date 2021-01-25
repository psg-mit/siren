val step =
  fun ((first, mu, sigma), (prob, obs)) ->
    let mu = if first then sample (prob, gaussian (0., 10.)) else mu in
    let sigma = if first then sample (prob, gaussian (0., 1.)) else sigma in
    let sigma2 = mult (sigma, sigma) in
    let () = observe (prob, (gaussian (mu, eval (sigma2)), obs)) in
    ((mu, sigma), (false, mu, sigma))

val main_init = infer_init (true, 0., 0.)
val main_step =
  fun ((first, mu, sigma), (prob, obs)) ->
    infer (
      fun ((first, mu, sigma), (prob, obs)) ->
        step ((first, mu, sigma), (prob, obs)),
      ((first, mu, sigma), (prob, obs))
    )
