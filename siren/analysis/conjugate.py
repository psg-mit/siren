from typing import Optional, Tuple

from siren.grammar import *
from siren.analysis.interface import AbsSymState

# If expr scales rv, returns the scaling factor
# Not complete
def is_scaled(state: AbsSymState, expr: AbsSymExpr, e: AbsSymExpr) -> Optional[AbsSymExpr]:
  if expr == e:
    return AbsConst(1)
  
  match expr:
    case Const(_):
      return None
    case RandomVar(_):
      return None
    case Add(e1, e2):
      s1 = is_scaled(state, e1, e)
      s2 = is_scaled(state, e2, e)
      if s1 is None or s2 is None:
        return None
      else:
        return state.ex_add(s1, s2)
    case Mul(e1, e2):
      s1 = is_scaled(state, e1, e)
      s2 = is_scaled(state, e2, e)
      if s1 is None and s2 is None:
        return None
      elif s1 is None and s2 is not None:
        return state.ex_mul(s2, e1)
      elif s1 is not None and s2 is None:
        return state.ex_mul(s1, e2)
      else:
        assert s1 is not None and s2 is not None
        return state.ex_mul(s1, s2)
    case Div(e1, e2):
      s1 = is_scaled(state, e1, e)
      s2 = is_scaled(state, e2, e)
      if s1 is not None and s2 is not None:
        return None # e cancels out
      elif s1 is None and s2 is not None:
        return state.ex_div(e1, s2)
      elif s1 is not None and s2 is None:
        return state.ex_div(s1, e2)
      else:
        return None
    case Ite(_):
      return None
    case Eq(_):
      return None
    case Lt(_):
      return None
    case Lst(_):
      return None
    case Pair(_):
      return None
    case _:
      raise ValueError(expr)

def abs_is_affine(state: AbsSymState, expr: AbsSymExpr, rv: AbsRandomVar) -> Optional[Tuple[AbsSymExpr, AbsSymExpr]]:
  match expr:
    case AbsConst(_):
      return (AbsConst(0), expr)
    case AbsRandomVar(_):
      if expr == rv:
        return (AbsConst(1), AbsConst(0))
      else:
        return (AbsConst(0), expr)
    case AbsAdd(e1, e2):
      coefs1 = abs_is_affine(state, e1, rv)
      coefs2 = abs_is_affine(state, e2, rv)
      if coefs1 is None or coefs2 is None:
        return None
      else:
        a1, b1 = coefs1
        a2, b2 = coefs2
        return (state.ex_add(a1, a2), state.ex_add(b1, b2))
    case AbsMul(e1, e2):
      coefs1 = abs_is_affine(state, e1, rv)
      coefs2 = abs_is_affine(state, e2, rv)
      if coefs1 is None or coefs2 is None:
        return None
      else:
        a1, b1 = coefs1
        a2, b2 = coefs2
        match state.eval(a1), state.eval(a2):
          case AbsConst(0), AbsConst(0):
            return (AbsConst(0), state.ex_mul(b1, b2))
          case a1, AbsConst(0):
            return (state.ex_mul(a1, b2), state.ex_mul(b1, b2))
          case AbsConst(0), a2:
            return (state.ex_mul(b1, a2), state.ex_mul(b1, b2))
          case _:
            return None
    case AbsDiv(e1, e2):
      coefs1 = abs_is_affine(state, e1, rv)
      coefs2 = abs_is_affine(state, e2, rv)
      if coefs1 is None or coefs2 is None:
        return None
      else:
        a1, b1 = coefs1
        a2, b2 = coefs2
        match state.eval(a2):
          case AbsConst(0):
            return (state.ex_div(a1, b2), state.ex_div(b1, b2))
          case _:
            return None
    case AbsIte(_):
      return None
    case AbsEq(_):
      return None
    case AbsLt(_):
      return None
    case AbsLst(_):
      return None
    case AbsPair(_):
      return None
    case UnkE(_):
      return None
    case _:
      raise ValueError(expr)
    
# Returns (marginal, posterior) distributions
def gaussian_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsNormal, AbsNormal]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsNormal(mu0, var0), AbsNormal(mu, var):
      coefs = abs_is_affine(state, mu, rv_par)
      if coefs is None:
        return None
      else:
        a, b = coefs
        if not mu0.depends_on(rv_child, True) \
          and not var0.depends_on(rv_child, True) \
          and not var.depends_on(rv_par, True):

          mu01 = state.ex_add(state.ex_mul(a, mu0), b)
          var01 = state.ex_mul(state.ex_mul(a, a), var0)

          denom = state.ex_add(state.ex_div(AbsConst(1), var01), state.ex_div(AbsConst(1), var))
          var02 = state.ex_div(AbsConst(1), denom)

          sum1 = state.ex_add(state.ex_div(mu01, var01), state.ex_div(rv_child, var))
          mu02 = state.ex_mul(sum1, var02)

          mu1_new = state.ex_div(state.ex_add(mu02, state.ex_mul(AbsConst(-1), b)), a)
          var1_new = state.ex_div(var02, state.ex_mul(a, a))

          mu0_new = mu01
          var0_new = state.ex_add(var01, var)

          return (AbsNormal(mu0_new, var0_new), AbsNormal(mu1_new, var1_new))
        else:
          return None
    case _:
      return None
    
def bernoulli_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsBernoulli, AbsBernoulli]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsBernoulli(p1), AbsBernoulli(p2):
      if p2.depends_on(rv_par, False) and \
        not p1.depends_on(rv_child, True):

        p2_new = state.ex_add(state.ex_mul(p1, p2.subst_rv(rv_par, AbsConst(True))),
                              state.ex_mul(state.ex_add(AbsConst(1), state.ex_mul(AbsConst(-1), p1)),
                                          p2.subst_rv(rv_par, AbsConst(False))))
        
        p1_num_sub = state.ex_ite(rv_child, p2, state.ex_add(AbsConst(1), state.ex_mul(AbsConst(-1), p2)))
        p1_num = state.ex_mul(p1, p1_num_sub.subst_rv(rv_par, AbsConst(True)))
        p1_denom = state.ex_ite(rv_child, p2_new, state.ex_add(AbsConst(1), state.ex_mul(AbsConst(-1), p2_new)))
        p1_new = state.ex_div(p1_num, p1_denom)

        return (AbsBernoulli(p2_new), AbsBernoulli(p1_new))
      else:
        return None
    case _:
      return None
    
def beta_bernoulli_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsBernoulli, AbsBeta]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsBeta(a, b), AbsBernoulli(p):
      if rv_par == p \
        and not a.depends_on(rv_child, True) \
        and not b.depends_on(rv_child, True):

        p_new = state.ex_div(a, state.ex_add(a, b))

        a_new = state.ex_add(a, state.ex_ite(rv_child, AbsConst(1), AbsConst(0)))
        b_new = state.ex_add(b, state.ex_ite(rv_child, AbsConst(0), AbsConst(1)))

        return (AbsBernoulli(p_new), AbsBeta(a_new, b_new))
      else:
        return None
    case _:
      return None
    
def beta_binomial_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsBetaBinomial, AbsBeta]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsBeta(a, b), AbsBinomial(n, p):
      if isinstance(n, AbsConst) \
        and isinstance(a, AbsConst)\
        and rv_par == p \
        and not a.depends_on(rv_child, True) \
        and not b.depends_on(rv_child, True):

        a_new = state.ex_add(a, rv_child)
        n_new = UnkC() if isinstance(n.v, UnkC) else float(n.v)
        b_new = state.ex_add(b, state.ex_add(AbsConst(n_new), state.ex_mul(AbsConst(-1), rv_child)))

        return (AbsBetaBinomial(n, a, b), AbsBeta(a_new, b_new))
      else:
        return None
    case _:
      return None
    
def gamma_poisson_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsNegativeBinomial, AbsGamma]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsGamma(a, b), AbsPoisson(l):
      # a is an integer 
      if isinstance(a, AbsConst) \
        and (isinstance(a.v, UnkC) or np.isclose(round(a.v), a.v)) \
        and rv_par == l \
        and not b.depends_on(rv_child, True):

        n_new = AbsConst(UnkC()) if isinstance(a.v, UnkC) else AbsConst(int(a.v)) 
        p_new = state.ex_div(b, state.ex_add(AbsConst(1), b))

        a_new = state.ex_add(a, rv_child)
        b_new = state.ex_add(b, AbsConst(1))

        return (AbsNegativeBinomial(n_new, p_new), AbsGamma(a_new, b_new))
      else:
        return None
    case _:
      return None
    
def gamma_normal_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsStudentT, AbsGamma]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsGamma(a, b), AbsNormal(mu, var):
      if isinstance(mu, AbsConst) \
        and var == state.ex_div(AbsConst(1), rv_par) \
        and not a.depends_on(rv_child, True) \
        and not b.depends_on(rv_child, True):

        tau2 = state.ex_div(b, a)
        nu = state.ex_mul(AbsConst(2), a)

        a_new = state.ex_add(a, AbsConst(0.5))
        b_inner = state.ex_add(rv_child, AbsConst(-mu.v))
        b_new = state.ex_add(b, state.ex_mul(AbsConst(0.5), 
                                            state.ex_mul(b_inner, b_inner)))
        
        return (AbsStudentT(mu, tau2, nu), AbsGamma(a_new, b_new))
      else:
        return None
    case _:
      return None
    
def normal_inverse_gamma_normal_conjugate(state: AbsSymState, rv_par: AbsRandomVar, rv_child: AbsRandomVar) -> Optional[Tuple[AbsStudentT, AbsNormal]]:
  prior, likelihood = state.distr(rv_par), state.distr(rv_child)
  match prior, likelihood:
    case AbsNormal(mu0, var1), AbsNormal(mu, var2):
      # var2 must be a random variable of invgamma
      # TODO: case of var2 being scaled invgamma
      match var2:
        case AbsDiv(AbsConst(1), var2_inner):
          if isinstance(var2_inner, AbsRandomVar):
            match state.distr(var2_inner):
              case AbsGamma(a, b):
                # var1 should be the invgamma scaled by 1/lambda
                k = is_scaled(state, var1, var2)
                if k is None:
                  return None
                else:
                  match state.eval(k):
                    case AbsConst(0):
                      return None
                    case AbsConst(_):
                      lam = state.ex_div(AbsConst(1), k)

                      if isinstance(mu0, Const) \
                        and mu == rv_par \
                        and not mu0.depends_on(rv_child, True) \
                        and not var1.depends_on(rv_child, True):

                        mu0_new = state.ex_div(state.ex_add(state.ex_mul(lam, mu0), rv_child), state.ex_add(lam, AbsConst(1)))
                        lam_new = state.ex_add(lam, AbsConst(1))
                        
                        a_new = state.ex_add(a, AbsConst(0.5))
                        b_inner = state.ex_add(rv_child, AbsConst(-mu0.v))
                        b_new = state.ex_add(b, state.ex_mul(state.ex_div(lam, state.ex_div(lam, AbsConst(1))), state.ex_div(state.ex_mul(b_inner, b_inner), AbsConst(2))))

                        state.set_distr(var2_inner, AbsGamma(a_new, b_new))

                        var_new = state.ex_div(AbsConst(1), state.ex_mul(lam_new, var2_inner))

                        mu_new = mu0
                        tau2_new = state.ex_div(state.ex_mul(b, state.ex_add(lam, AbsConst(1))), state.ex_mul(a, lam))
                        nu_new = state.ex_mul(AbsConst(2), a)

                        return (AbsStudentT(mu_new, tau2_new, nu_new), AbsNormal(mu0_new, var_new))
                    case _:
                      return None
              case _:
                return None
          else:
            return None
        case _:
          return None
    case _:
      return None