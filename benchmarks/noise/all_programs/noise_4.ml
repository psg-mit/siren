open Probzelus
open Distribution
open Muf
open Infer_muf

let preprocess_data entry muf_k =
  (fun v2 -> (List.tl v2) (fun v1 -> (List.hd v1) muf_k)) entry
let step (acc, zobs) muf_k =
  (fun v40 ->
     (fun v3 ->
        let (xs, acc) = v3 in
        (fun v39 ->
           (fun v4 ->
              let (q, r) = v4 in
              (fun v38 ->
                 (List.hd v38)
                   (fun v5 ->
                      let prev_x = v5 in
                      (fun v6 ->
                         let h = v6 in
                         (fun v7 ->
                            let f = v7 in
                            (fun v36 ->
                               (fun v37 ->
                                  (fun v35 ->
                                     (fun v30 ->
                                        (fun v33 ->
                                           (fun v34 ->
                                              (fun v32 ->
                                                 (fun v31 ->
                                                    (fun v29 ->
                                                       (fun v28 ->
                                                          (sample "step_x"
                                                             v28)
                                                            (fun v27 ->
                                                               (fun v8 ->
                                                                  let x = v8 in
                                                                  (fun v25 ->
                                                                    (fun v26
                                                                    ->
                                                                    (fun v24
                                                                    ->
                                                                    (fun v19
                                                                    ->
                                                                    (fun v22
                                                                    ->
                                                                    (fun v23
                                                                    ->
                                                                    (fun v21
                                                                    ->
                                                                    (fun v20
                                                                    ->
                                                                    (fun v18
                                                                    ->
                                                                    (fun v16
                                                                    ->
                                                                    (fun v17
                                                                    ->
                                                                    (observe
                                                                    v16 v17)
                                                                    (fun v9
                                                                    ->
                                                                    let (_unit_v41
                                                                    :
                                                                    unit expr)
                                                                    = v9 in
                                                                    (fun v14
                                                                    ->
                                                                    (fun v15
                                                                    ->
                                                                    (fun v13
                                                                    ->
                                                                    (List.cons
                                                                    v13)
                                                                    (fun v10
                                                                    ->
                                                                    (fun v11
                                                                    ->
                                                                    (fun v12
                                                                    ->
                                                                    muf_k
                                                                    (pair v10
                                                                    (pair v11
                                                                    v12))) r)
                                                                    q))
                                                                    (v14,
                                                                    v15)) xs)
                                                                    x)) zobs)
                                                                    (gaussian
                                                                    v18))
                                                                    (v19,
                                                                    v20))
                                                                    (div v21))
                                                                    (v22,
                                                                    v23)) r)
                                                                    (const 1.))
                                                                    (mul v24))
                                                                    (v25,
                                                                    v26))
                                                                    prev_x) h)
                                                                 (value v27)))
                                                         (gaussian v29))
                                                      (v30, v31)) (div v32))
                                                (v33, v34)) q) (const 1.))
                                       (mul v35)) (v36, v37)) prev_x) f)
                           (const 1.001)) (const 2.))) xs) (split v39)) acc)
       (split v40)) acc
let output out =
  let (xs, out) = split out in
  let (q, r) = split out in
  let (_unit_v46 : unit expr) = Print.print_float (mean_float q) in
  let (_unit_v45 : unit expr) = Print.print_endline (const ()) in
  let (_unit_v44 : unit expr) = Print.print_float (mean_float r) in
  let (_unit_v43 : unit expr) = Print.print_endline (const ()) in
  let (_unit_v42 : unit expr) = Print.print_float_list2 xs in const ()
let main _ muf_k =
  (fun v80 ->
     (fun v82 ->
        (fun v81 ->
           (fun v79 ->
              (List.map v79)
                (fun v47 ->
                   let data = v47 in
                   (fun v77 ->
                      (fun v78 ->
                         (fun v76 ->
                            (fun v75 ->
                               (sample "q" v75)
                                 (fun v48 ->
                                    let q = v48 in
                                    (fun v73 ->
                                       (fun v74 ->
                                          (fun v72 ->
                                             (fun v71 ->
                                                (sample "r" v71)
                                                  (fun v49 ->
                                                     let r = v49 in
                                                     (fun v50 ->
                                                        let x0 = v50 in
                                                        (fun v64 ->
                                                           (fun v65 ->
                                                              (fun v70 ->
                                                                 (fun v67 ->
                                                                    (fun v68
                                                                    ->
                                                                    (fun v69
                                                                    ->
                                                                    (fun v66
                                                                    ->
                                                                    (fun v63
                                                                    ->
                                                                    (List.fold_resample
                                                                    v63)
                                                                    (fun v51
                                                                    ->
                                                                    let out =
                                                                    v51 in
                                                                    (fun v62
                                                                    ->
                                                                    (fun v52
                                                                    ->
                                                                    let 
                                                                    (xs, out)
                                                                    = v52 in
                                                                    (fun v61
                                                                    ->
                                                                    (fun v53
                                                                    ->
                                                                    let 
                                                                    (q, r) =
                                                                    v53 in
                                                                    (fun v60
                                                                    ->
                                                                    (List.rev
                                                                    v60)
                                                                    (fun v54
                                                                    ->
                                                                    let xs =
                                                                    v54 in
                                                                    (fun v59
                                                                    ->
                                                                    (List.tl
                                                                    v59)
                                                                    (fun v55
                                                                    ->
                                                                    let xs =
                                                                    v55 in
                                                                    (fun v56
                                                                    ->
                                                                    (fun v57
                                                                    ->
                                                                    (fun v58
                                                                    ->
                                                                    muf_k
                                                                    (pair v56
                                                                    (pair v57
                                                                    v58))) r)
                                                                    q) xs))
                                                                    xs)) xs)
                                                                    (split
                                                                    v61)) out)
                                                                    (split
                                                                    v62)) out))
                                                                    (v64,
                                                                    v65, v66))
                                                                    (pair v67
                                                                    (pair v68
                                                                    v69))) r)
                                                                    q)
                                                                   (lst [v70]))
                                                                x0) data)
                                                          step) (const 0.)))
                                               (gamma v72)) (v73, v74))
                                         (const 1.)) (const 1.))) (gamma v76))
                           (v77, v78)) (const 1.)) (const 1.))) (v80, v81))
          (read v82)) (const "data/processed_data.csv")) preprocess_data
let post_main _ = 
  let () = Format.printf "==== OUTPUT ====\n" in
  let _ = infer 1 main (Some output) in
  let () = Format.printf "\n==== RUNTIME APPROXIMATION STATUS ====\n" in
  let () = Format.printf "%s\n" (pp_approx_status false) in ()
let _ =
  post_main ()
