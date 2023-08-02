open Probzelus
open Distribution
open Muf
open Infer_muf

let preprocess_data entry muf_k =
  (fun v2 -> (List.tl v2) (fun v1 -> (List.hd v1) muf_k)) entry
let step (prev, yobs) muf_k =
  (fun v39 ->
     (fun v3 ->
        let (first, prev) = v3 in
        (fun v38 ->
           (fun v4 ->
              let (outlier_prob, prev_xt) = v4 in
              (fun v35 ->
                 (fun v36 ->
                    (fun v37 ->
                       (fun v5 ->
                          let xt_mu = v5 in
                          (fun v32 ->
                             (fun v33 ->
                                (fun v34 ->
                                   (fun v6 ->
                                      let xt_var = v6 in
                                      (fun v30 ->
                                         (fun v31 ->
                                            (fun v29 ->
                                               (fun v28 ->
                                                  (sample "step_xt" v28)
                                                    (fun v7 ->
                                                       let xt = v7 in
                                                       (fun v27 ->
                                                          (fun v26 ->
                                                             (sample
                                                                "step_is_outlier"
                                                                v26)
                                                               (fun v8 ->
                                                                  let is_outlier
                                                                    = v8 in
                                                                  (fun v23 ->
                                                                    (fun v24
                                                                    ->
                                                                    (fun v25
                                                                    ->
                                                                    (fun v9
                                                                    ->
                                                                    let mu =
                                                                    v9 in
                                                                    (fun v20
                                                                    ->
                                                                    (fun v21
                                                                    ->
                                                                    (fun v22
                                                                    ->
                                                                    (fun v10
                                                                    ->
                                                                    let var =
                                                                    v10 in
                                                                    (fun v18
                                                                    ->
                                                                    (fun v19
                                                                    ->
                                                                    (fun v17
                                                                    ->
                                                                    (fun v15
                                                                    ->
                                                                    (fun v16
                                                                    ->
                                                                    (observe
                                                                    v15 v16)
                                                                    (fun v11
                                                                    ->
                                                                    let (_unit_v40
                                                                    :
                                                                    unit expr)
                                                                    = v11 in
                                                                    (fun v12
                                                                    ->
                                                                    (fun v13
                                                                    ->
                                                                    (fun v14
                                                                    ->
                                                                    muf_k
                                                                    (pair v12
                                                                    (pair v13
                                                                    v14))) xt)
                                                                    outlier_prob)
                                                                    (const
                                                                    false)))
                                                                    yobs)
                                                                    (gaussian
                                                                    v17))
                                                                    (v18,
                                                                    v19)) var)
                                                                    mu)
                                                                    (ite v20
                                                                    v21 v22))
                                                                    (const 1.))
                                                                    (const
                                                                    10000.))
                                                                    is_outlier)
                                                                    (ite v23
                                                                    v24 v25))
                                                                    xt)
                                                                    (const 0.))
                                                                    is_outlier))
                                                            (bernoulli v27))
                                                         outlier_prob))
                                                 (gaussian v29)) (v30, v31))
                                           xt_var) xt_mu) (ite v32 v33 v34))
                                  (const 1.)) (const 2500.)) first)
                         (ite v35 v36 v37)) prev_xt) (const 0.)) first)
             (split v38)) prev) (split v39)) prev
let output out =
  let (outlier_prob, x) = split out in
  let (_unit_v43 : unit expr) = Print.print_float (mean_float outlier_prob) in
  let (_unit_v42 : unit expr) = Print.print_endline (const ()) in
  let (_unit_v41 : unit expr) = Print.print_float (mean_float x) in const ()
let main _ muf_k =
  (fun v65 ->
     (fun v67 ->
        (fun v66 ->
           (fun v64 ->
              (List.map v64)
                (fun v44 ->
                   let data = v44 in
                   (fun v62 ->
                      (fun v63 ->
                         (fun v61 ->
                            (fun v60 ->
                               (sample "outlier_prob" v60)
                                 (fun v59 ->
                                    (fun v45 ->
                                       let outlier_prob = v45 in
                                       (fun v53 ->
                                          (fun v54 ->
                                             (fun v56 ->
                                                (fun v57 ->
                                                   (fun v58 ->
                                                      (fun v55 ->
                                                         (fun v52 ->
                                                            (List.fold_resample
                                                               v52)
                                                              (fun v51 ->
                                                                 (fun v46 ->
                                                                    let 
                                                                    (_, res)
                                                                    = v46 in
                                                                    (fun v50
                                                                    ->
                                                                    (fun v47
                                                                    ->
                                                                    let 
                                                                    (outlier_prob,
                                                                    x) = v47 in
                                                                    (fun v48
                                                                    ->
                                                                    (fun v49
                                                                    ->
                                                                    muf_k
                                                                    (pair v48
                                                                    v49)) x)
                                                                    outlier_prob)
                                                                    (split
                                                                    v50)) res)
                                                                   (split v51)))
                                                           (v53, v54, v55))
                                                        (pair v56
                                                           (pair v57 v58)))
                                                     (const 0.)) outlier_prob)
                                               (const true)) data) step)
                                      (value v59))) (beta v61)) (v62, v63))
                        (const 1000.)) (const 100.))) (v65, v66)) (read v67))
       (const "data/processed_data.csv")) preprocess_data
let post_main _ = 
  let () = Format.printf "==== OUTPUT ====\n" in
  let _ = infer 1 main (Some output) in
  let () = Format.printf "\n==== RUNTIME APPROXIMATION STATUS ====\n" in
  let () = Format.printf "%s\n" (pp_approx_status false) in ()
let _ =
  post_main ()
