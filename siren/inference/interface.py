from typing import Dict, Tuple, Optional, Set
from copy import copy
import warnings

from siren.grammar import *
from siren.utils import is_pair, is_lst, get_pair, get_lst

class RuntimeViolatedAnnotationError(Exception):
  pass

class SymState(object):
  def __init__(self, seed=None) -> None:
    super().__init__()
    self.state: Dict[RandomVar, Tuple[Optional[Identifier], SymDistr]] = {}
    self.ctx: Context = Context()
    self.counter: int = 0
    self.annotations: Dict[Identifier, Annotation] = {}
    self.rng = np.random.default_rng(seed=seed)

  def __copy__(self):
    new_state = type(self)()
    new_state.state = copy(self.state)
    new_state.ctx = copy(self.ctx)
    new_state.counter = self.counter
    new_state.annotations = self.annotations
    new_state.rng = self.rng
    return new_state

  def new_var(self) -> RandomVar:
    self.counter += 1
    return RandomVar(f"rv{self.counter}")
  
  def vars(self) -> Set[RandomVar]:
    return set(self.state.keys())
    
  def distr(self, variable: RandomVar[T]) -> SymDistr[T]:
    return self.state[variable][1]
  
  def pv(self, variable: RandomVar) -> Optional[Identifier]:
    return self.state[variable][0]
  
  def set_distr(self, variable: RandomVar[T], distribution: SymDistr[T]) -> None:
    # Check if annotations violated
    if isinstance(distribution, Delta):
      pv = self.pv(variable)
      if pv in self.annotations and self.annotations[pv] == Annotation.symbolic \
        and distribution.sampled:
        raise RuntimeViolatedAnnotationError(
          f"{self.pv(variable)} is annotated as symbolic but will be sampled")
      
    self.state[variable] = (self.state[variable][0], distribution)

  def is_sampled(self, variable: RandomVar) -> bool:
    match self.distr(variable):
      case Delta(_, sampled):
        return sampled
      case _:
        return False

  def __len__(self) -> int:
    return len(self.state)

  def __iter__(self):
    return iter(self.state)
  
  def __str__(self):
    return f"SymState({', '.join(map(str, self.state.items()))})"
  
  def clean(self) -> None:
    used_vars = set().union(*(expr.rvs() for expr in self.ctx.context.values()))
    # get referenced vars in the distribution of each ctx variable
    while True:
      new_used_vars = used_vars | set().union(*(self.distr(rv).rvs() for rv in used_vars))
      if new_used_vars == used_vars:
        used_vars = new_used_vars
        break
      else:
        used_vars = new_used_vars

    # remove unused variables
    for rv in self.vars():
      if rv not in used_vars:
        del self.state[rv]

  def str_distrs(self, rv: RandomVar) -> str:
    distr = self.eval(rv)
    match self.distr(rv):
      case Normal(mu, var):
        return f"Normal({self.str_expr(mu)}, {self.str_expr(var)})"
      case Bernoulli(p):
        return f"Bernoulli({self.str_expr(p)})"
      case Beta(a, b):
        return f"Beta({self.str_expr(a)}, {self.str_expr(b)})"
      case Binomial(n, p):
        return f"Binomial({self.str_expr(n)}, {self.str_expr(p)})"
      case BetaBinomial(n, a, b):
        return f"BetaBinomial({self.str_expr(n)}, {self.str_expr(a)}, {self.str_expr(b)})"
      case NegativeBinomial(n, p):
        return f"NegativeBinomial({self.str_expr(n)}, {self.str_expr(p)})"
      case Gamma(a, b):
        return f"Gamma({self.str_expr(a)}, {self.str_expr(b)})"
      case Poisson(l):
        return f"Poisson({self.str_expr(l)})"
      case StudentT(mu, tau2, nu):
        return f"StudentT({self.str_expr(mu)}, {self.str_expr(tau2)}, {self.str_expr(nu)})"
      case Categorical(lower, upper, probs):
        return f"Categorical({self.str_expr(lower)}, {self.str_expr(upper)}, {self.str_expr(probs)})"
      case Delta(v, sampled):
        return f"Delta({self.str_expr(v)}, {sampled})"
      case _:
        raise ValueError(self.distr(rv))

  def str_expr (self, expr: SymExpr) -> str:
    expr = self.eval(expr)
    match expr:
      case Const(value):
        return str(value)
      case RandomVar(_):
        return self.str_distrs(expr)
      case Add(left, right):
        return f"({self.str_expr(left)} + {self.str_expr(right)})"
      case Mul(left, right):
        return f"({self.str_expr(left)} * {self.str_expr(right)})"
      case Div(left, right):
        return f"({self.str_expr(left)} / {self.str_expr(right)})"
      case Ite(cond, true, false):
        return f"ite({self.str_expr(cond)}, {self.str_expr(true)}, {self.str_expr(false)})"
      case Lst(es):
        return f"[{', '.join(map(self.str_expr, es))}]"
      case Pair(e1, e2):
        return f"({self.str_expr(e1)}, {self.str_expr(e2)})"
      case _:
        raise ValueError(expr)
  
  
  def ex_add(self, e1: SymExpr[Number], e2: SymExpr[Number]) -> SymExpr[Number]:
    match e1, e2:
      case Const(v1), Const(v2):
        return Const(v1 + v2)
      case Const(v1), Add(Const(v2), e3):
        return self.ex_add(Const(v1 + v2), e3) 
      case Const(v1), Add(e2, Const(v3)):
        return self.ex_add(Const(v1 + v3), e2)
      case Add(Const(v1), e2), e3:
        return self.ex_add(Const(v1), self.ex_add(e2, e3))
      case Const(0), e2:
        return e2
      case e1, Const(0):
        return e1
      case _:
        return Add(e1, e2)

  def ex_mul(self, e1: SymExpr[Number], e2: SymExpr[Number]) -> SymExpr[Number]:
    match e1, e2:
      case Const(v1), Const(v2):
        return Const(v1 * v2)
      case Const(v1), Mul(Const(v2), e3):
        return self.ex_mul(Const(v1 * v2), e3)
      case Const(v1), Mul(e2, Const(v3)):
        return self.ex_mul(Const(v1 * v3), e2)
      case Const(v1), Add(Const(v2), e3):
        return self.ex_add(Const(v1 * v2), self.ex_mul(Const(v1), e3))
      case Const(0), _:
        return Const(0)
      case _, Const(0):
        return Const(0)
      case _:
        return Mul(e1, e2)

  def ex_div(self, e1: SymExpr[Number], e2: SymExpr[Number]) -> SymExpr[Number]:
    match e1, e2:
      case Const(v1), Const(v2):
        return Const(v1 / v2)
      case e1, Const(1):
        return e1
      case _:
        return Div(e1, e2)

  def ex_ite(self, cond: SymExpr[bool], true: SymExpr[T], false: SymExpr[T]) -> SymExpr[T]:
    match cond:
      case Const(v):
        return true if v else false
      case _:
        return Ite(cond, true, false)

  def ex_eq(self, e1: SymExpr[T], e2: SymExpr[T]) -> SymExpr[bool]:
    match e1, e2:
      case Const(v1), Const(v2):
        return Const(v1 == v2)
      case _:
        return Eq(e1, e2)

  def ex_lt(self, e1: SymExpr[Number], e2: SymExpr[Number]) -> SymExpr[bool]:
    match e1, e2:
      case Const(v1), Const(v2):
        return Const(v1 < v2)
      case _:
        return Lt(e1, e2)

  def eval(self, expr: SymExpr) -> SymExpr:
    def _const_list(es: List[SymExpr]) -> Optional[Const[List[SymExpr]]]:
      consts = []
      for e in es:
        if not isinstance(e, Const):
          return None
        consts.append(e.v)

      return Const(consts)
    
    def _eval(expr: SymExpr) -> SymExpr:
      match expr:
        case Const(_):
          return expr
        case RandomVar(_):
          match self.distr(expr):
            case Delta(v, _):
              return _eval(v)
            case _:
              self.set_distr(expr, self.eval_distr(self.distr(expr)))
              return expr
        case Add(e1, e2):
          return self.ex_add(_eval(e1), _eval(e2))
        case Mul(e1, e2):
          return self.ex_mul(_eval(e1), _eval(e2))
        case Div(e1, e2):
          return self.ex_div(_eval(e1), _eval(e2))
        case Ite(cond, true, false):
          return self.ex_ite(_eval(cond), _eval(true), _eval(false))
        case Eq(e1, e2):
          return self.ex_eq(_eval(e1), _eval(e2))
        case Lt(e1, e2):
          return self.ex_lt(_eval(e1), _eval(e2))
        case Lst(es):
          es = [self.eval(e) for e in es]
          const_list = _const_list(es)
          return const_list if const_list is not None else Lst(es)
        case Pair(e1, e2):
          e1, e2 = self.eval(e1), self.eval(e2)
          match e1, e2:
            case Const(_), Const(_):
              return Const((e1.v, e2.v))
            case _:
              return Pair(e1, e2)
        case _:
          raise ValueError(expr)

    return _eval(expr)

  def eval_distr(self, distr: SymDistr) -> SymDistr:
    match distr:
      case Normal(mu, var):
        return Normal(self.eval(mu), self.eval(var))
      case Bernoulli(p):
        return Bernoulli(self.eval(p))
      case Beta(a, b):
        return Beta(self.eval(a), self.eval(b))
      case Binomial(n, p):
        return Binomial(self.eval(n), self.eval(p))
      case BetaBinomial(n, a, b):
        return BetaBinomial(self.eval(n), self.eval(a), self.eval(b))
      case NegativeBinomial(n, p):
        return NegativeBinomial(self.eval(n), self.eval(p))
      case Gamma(a, b):
        return Gamma(self.eval(a), self.eval(b))
      case Poisson(l):
        return Poisson(self.eval(l))
      case StudentT(mu, tau2, nu):
        return StudentT(self.eval(mu), self.eval(tau2), self.eval(nu))
      case Categorical(lower, upper, probs):
        return Categorical(self.eval(lower), self.eval(upper), self.eval(probs))
      case Delta(v, sampled):
        return Delta(self.eval(v), sampled)
      case _:
        raise ValueError(distr)

  
  def marginalize(self, expr: RandomVar) -> None:
    raise NotImplementedError()
      
  def value_expr(self, expr: SymExpr) -> Const:
    match expr:
      case Const(_):
        return expr
      case RandomVar(_):
        return self.value(expr)
      case Add(fst, snd):
        return Const(self.value_expr(fst).v + self.value_expr(snd).v)
      # case Sub(fst, snd):
      #   fst = value(fst, state).v
      #   snd = value(snd, state).v
      #   if (isinstance(fst, float) and isinstance(snd, float)) or \
      #     isinstance(fst, int) and isinstance(snd, int):
      #     return Const(fst - snd)
      #   else:
      #     raise ValueError(fst, snd)
      case Mul(fst, snd):
        return Const(self.value_expr(fst).v * self.value_expr(snd).v)
      case Div(fst, snd):
        return Const(self.value_expr(fst).v / self.value_expr(snd).v)
      case Ite(cond, true, false):
        cond = self.value_expr(cond).v
        if isinstance(cond, bool):
          if cond:
            return self.value_expr(true)
          else:
            return self.value_expr(false)
        else:
          raise ValueError(cond)
      case Eq(fst, snd):
        fst = self.value_expr(fst).v
        snd = self.value_expr(snd).v
        return Const(fst == snd)
      case Lt(fst, snd):
        fst = self.value_expr(fst).v
        snd = self.value_expr(snd).v
        return Const(fst < snd)
      case Lst(es):
        return Const([self.value_expr(e) for e in es])
      case Pair(e1, e2):
        return Const((self.value_expr(e1), self.value_expr(e2)))
      case _:
        raise ValueError(expr)
  
  def assume(self, name: Optional[Identifier], annotation: Optional[Annotation], distribution: SymDistr[T]) -> RandomVar[T]:
    raise NotImplementedError()

  def observe(self, rv: RandomVar[T], value: Const[T]) -> float:
    raise NotImplementedError()

  def value(self, rv: RandomVar[T]) -> Const[T]:
    raise NotImplementedError()
      
class Context(object):
  def __init__(self, init={}) -> None:
    super().__init__()
    self.context: Dict[Identifier, SymExpr] = init

  def __getitem__(self, identifier: Identifier) -> Expr:
    return self.context[identifier]

  def __setitem__(self, identifier: Identifier, value: SymExpr) -> None:
    self.context[identifier] = value

  def __len__(self) -> int:
    return len(self.context)

  def __iter__(self):
    return iter(self.context)

  def __or__(self, other: 'Context') -> 'Context':
    return Context({**self.context, **other.context})

  def __str__(self) -> str:
    return f"Context({', '.join(map(str, self.context.items()))})"
  
  def temp_var(self, name: str="x") -> Identifier:
    i = 0
    while True:
      identifier = Identifier(None, f"{name}_{i}")
      if identifier not in self:
        return identifier
      i += 1

class Particle(object):
  def __init__(
    self, cont: Expr[SymExpr], 
    state: SymState = SymState(),
    score: float = 0.,
    finished: bool = False,
  ) -> None:
    super().__init__()
    self.cont: Expr[SymExpr] = cont
    self.state: SymState = state
    self.score: float = score  # logscale
    self.finished: bool = finished

  @property
  def final_expr(self) -> SymExpr:
    if self.finished:
      assert isinstance(self.cont, SymExpr)
      return self.cont
    else:
      raise ValueError(f'Particle not finished: {self}')
    
  def update(self, cont: Optional[Expr] = None,
              state: Optional[SymState] = None, 
              score: Optional[float] = None,
              finished: Optional[bool] = None) -> 'Particle':
    if cont is not None:
      self.cont = cont
    if state is not None:
      self.state = state
    if score is not None:
      self.score = score
    if finished is not None:
      self.finished = finished
    return self

  def __str__(self):
    return f"Particle({self.cont}, {self.state}, {self.score}, {self.finished})"
  
  def __copy__(self) -> 'Particle':
    return Particle(
      self.cont,
      copy(self.state),
      self.score,
      self.finished,
    )
  
  def simplify(self) -> 'Particle':
    for rv in self.state.vars():
      self.state.set_distr(rv, self.state.eval_distr(self.state.distr(rv)))
    return self

class Mixture(object):
  def __init__(self, mixture: List[Tuple[SymExpr, SymState, float]]):
    super().__init__()
    if len(mixture) == 0:
      raise ValueError("Empty distribution")
    self.mixture: List[Tuple[SymExpr, SymState, float]] = mixture

  def __str__(self) -> str:
    s = '\n'.join([f"{state.str_expr(expr)}: {prob}" for expr, state, prob in self.mixture])
    return f"Mixture(\n{s}\n)"
  
  def __repr__(self) -> str:
    return self.__str__()
  
  def __len__(self) -> int:
    return len(self.mixture)
  
  def __iter__(self):
    return iter(self.mixture)
  
  def __getitem__(self, index: int) -> Tuple[SymExpr, SymState, float]:
    return self.mixture[index]
  
  def __setitem__(self, index: int, value: Tuple[SymExpr, SymState, float]) -> None:
    self.mixture[index] = value

  @property
  def is_pair_mixture(self) -> bool:
    if len(self.mixture) == 0:
      raise ValueError("No results")
    return all(is_pair(expr) for expr, _, _ in self.mixture)

  def get_pair_mixture(self) -> Tuple['Mixture', 'Mixture']:
    if len(self.mixture) == 0:
      raise ValueError("No results")
    fst, snd = [], []
    for expr, state, weight in self.mixture:
      f, s = get_pair(expr)
      fst.append((f, state, weight))
      snd.append((s, state, weight))
    return Mixture(fst), Mixture(snd)

  @property
  def is_lst_mixture(self) -> bool:
    if len(self.mixture) == 0:
      raise ValueError("No results")
    return all(is_lst(expr) for expr, _, _ in self.mixture)

  def get_lst_mixture(self) -> List['Mixture']:
    if len(self.mixture) == 0:
      raise ValueError("No results")
    all_lsts = [(get_lst(expr), s, w) for expr, s, w in self.mixture]
    max_len = max(len(lst) for lst, _, _ in all_lsts)
    acc = []
    for i in range(max_len):
      acc.append([])
      for lst, state, weight in all_lsts:
        if i < len(lst):
          acc[i].append((lst[i], state, weight))
    return list(map(lambda x: Mixture(x), acc))
      
  def mean(self) -> float:
    if len(self.mixture) == 0:
      raise ValueError("No results")
    if len(self.mixture) == 1:
      return mean(self.mixture[0][0], self.mixture[0][1])
    acc = 0.0
    for expr, state, weight in self.mixture:
      acc += weight * mean(expr, state)
    return acc

def mean(expr: SymExpr, state: SymState) -> float:
  expr = state.eval(expr)

  match expr:
    case Const(value):
      return value
    case RandomVar(_):
      state.marginalize(expr)
      return state.distr(expr).mean()
    case Add(left, right):
      return mean(left, state) + mean(right, state)
    # case Sub(left, right):
    #   return mean(left, state) - mean(right, state)
    case Mul(left, right):
      return mean(left, state) * mean(right, state)
    case Div(left, right):
      return mean(left, state) / mean(right, state)
    case Ite(cond, true, false):
      return mean(true, state) if mean(cond, state) else mean(false, state)
    case _:
      raise ValueError(expr)

class ProbState(object):
  def __init__(self, n_particles: int, cont: Expr, method: type[SymState], seed: Optional[int] = None) -> None:
    super().__init__()
    self.rng = np.random.default_rng(seed=seed)
    self.particles: List[Particle] = [
      Particle(cont, method(seed=seed)) for i in range(n_particles)
    ]

  def __getitem__(self, index: int) -> Particle:
    return self.particles[index]

  def __setitem__(self, index: int, value: Particle) -> None:
    self.particles[index] = value

  def __len__(self) -> int:
    return len(self.particles)

  def __iter__(self):
    return iter(self.particles)
  
  def simplify(self) -> 'ProbState':
    for p in self.particles:
      p.simplify()
    return self

  def __str__(self) -> str:
    particles_indices = {}
    for i, p in enumerate(self.particles):
      key = str(p)
      if key not in particles_indices:
        particles_indices[key] = [i]
      else:
        particles_indices[key].append(i)

    return "\n".join([f"{str(indices)}: {p}" for p, indices in particles_indices.items()])
    
    # return "\n".join([f"{i}: {p}" for i, p in enumerate(self.particles)])
  
  def normalized_probabilities(self) -> List[float]:
    scores = np.array([p.score for p in self.particles])
    if np.max(scores) == -np.inf:
      warnings.warn("All particles have 0 weight")
      scores = np.zeros(len(scores))
      # raise RuntimeError("All particles have 0 weight")
    probabilities = np.exp(scores - np.max(scores))
    return list(probabilities / probabilities.sum())
  
  def mixture(self) -> Mixture:
    probabilities = self.normalized_probabilities()
    values = [p.final_expr for p in self.particles]
    states = [copy(p.state) for p in self.particles]

    unique_values = {}
    for v, state, prob in zip(values, states, probabilities):
      v = state.eval(v)
      key = str(v)
      
      if key not in unique_values:
        unique_values[key] = (v, state, prob)
      else:
        unique_values[key] = (v, state, unique_values[key][2] + prob)
    unique_values = Mixture(list(unique_values.values()))

    return unique_values

  def result(self) -> SymExpr:
    unique_values = self.mixture()
    
    def _get_mean(res: Mixture) -> Const:
      if res.is_pair_mixture:
        fst, snd = res.get_pair_mixture()
        fst = _get_mean(fst)
        snd = _get_mean(snd)
        return Const((fst.v, snd.v))
      elif res.is_lst_mixture:
        lst = res.get_lst_mixture()
        return Const(list(map(lambda x: _get_mean(x).v, lst)))
      else:
        return Const(res.mean())
      
    return _get_mean(unique_values)

  @property
  def finished(self) -> bool:
    return all(p.finished for p in self.particles)
  
  def resample(self) -> 'ProbState':
    particles = self.particles
    probabilities = self.normalized_probabilities()
    idxs = self.rng.choice(np.arange(len(particles)), size=len(particles),
                            replace=True, p=probabilities)
    used_idxs = set()
    new_particles = []
    for idx in idxs:
      if idx not in used_idxs:
        new_particles.append(particles[idx])
        used_idxs.add(idx)
      else:
        new_particles.append(copy(particles[idx]))
    self.particles = new_particles
    for p in self.particles:
      p.update(score=0.)
    return self
  