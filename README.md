# Drive-Based Embodied Agent

An attempt to build an embodied, human-like artificial agent whose behavior is **downstream of hardcoded drives**, not scripted and not borrowed from human text. The agent is given a small set of built-in needs and motivations; its preferences, "emotions," and decisions are meant to *emerge* from those needs interacting with a world.

This is a long-horizon research project. This README describes the full intended architecture, but the **only thing being built right now is Phase 0** (see below). Everything past Phase 0 is recorded here as direction, not as work in progress.

---

## Core thesis

The wanting comes first. The agent always has the same basic needs (energy, safety, etc.) and the same basic motivations (curiosity, play). It does not look at the world and then decide what to want — it always already wants these things, and perception only tells it *how those standing wants apply to the current situation*.

Two consequences drive every design decision:

1. **No exogenous goals.** The agent's purposes come from its own drives, not from a human instruction or a hand-specified reward for each task. This is the main thing separating this project from a conventional goal-following robot or an instruction-following model.
2. **No LLM in the value path.** A language model trained on human text encodes the *finished conclusions* of human cognition (concepts, preferences, values). Injecting that hands the agent the answers to the very thing we want it to derive for itself. A reasoning component may exist (see Architecture), but it is strictly quarantined to generating/forecasting options and may never produce value or decide.

---

## Architecture (full, eventual)

The system is a loop. One pass = one decision cycle.

```
                          senses in
                              |
                        [ Perceive present ]   builds a picture of the
                              |                 current situation from senses
        standing             |
        valuation            v
   +----------------+   [ Reasoning ]   what & where  (slow clock, sets goals)
   |  Drive core    |        | ^
   |  (the WHY)     |   goal | | status
   +----------------+        v |
          |            [ Predictive model ]   how  (fast, moment-to-moment)
          | needs            |
          v                  | imagined futures
   +----------------+        v
   |  Affect        |--> [ Decision layer ]   scores imagined futures in drive
   |  (sets mood)   | tunes      |             currency, picks one
   +----------------+            | first action
                                 v
                         [ Motor system ]   executes first step only
                                 |
                         acts on world, loops back to senses
```

Memory sits to the side of the planning stack (Reasoning + Predictive), queried by relevance — it is a store, not a stage in the loop.

### The boxes, and what each is for

**Drive core — the WHY.** Holds the agent's needs as an explicit, small, named state (e.g. `energy`, `temperature`, `social`). Each need has a setpoint and a notion of urgency that grows nonlinearly as the need leaves its viable range. Two *kinds* of drive:

- **Deficit drives** (energy, threat-avoidance, social-when-lonely): spike when a variable leaves its healthy range, go quiet when satisfied. These produce purposeful, need-correcting behavior.
- **Open-ended drives** (curiosity, play, competence): never fully satisfied; their target is a *rate* (keep encountering learnable novelty), not a level. These are what keep the agent active when nothing is wrong. Without them you get an agent that goes inert the moment its needs are met.

The drive core outputs **value, not commands** — a readout of what is needed and how badly, plus a value function that scores any state by how close it is to the setpoints. It is the one component written and verified by hand; everything downstream inherits its correctness.

**Affect — the mood.** *Not* a stored need. A **function of** the drive state and recent prediction-error statistics that returns a set of modulation parameters: planning horizon, caution vs. boldness, how much to explore, how strongly to react. Affect does not add wants — it changes *how* the existing wants are pursued. (Frightened-and-hungry forages differently from calm-and-hungry; the need is identical, the mood differs.) Recomputed each cycle; never stored as a field alongside the needs.

**World model (Perceive + Predictive).** The agent's imagination. Two linked jobs:

- *Perceive present:* infer the current situation from partial, noisy senses — including things not directly sensed. (Eventually a fill-in / inference model over a learned representation; in Phase 0, trivial.)
- *Predictive model:* given the current state and a candidate action, predict the **likely range** of resulting states (a distribution, not one certain future). Low-altitude, fast, concrete — works in the immediate terms of the body and the world right in front of it. Rolls forward only short horizons; compounding error makes long rollouts useless, which is *why* the reasoning layer exists.

These two form a feedback loop: perception feeds prediction, and prediction error corrects perception. They are functional roles, not necessarily separate networks.

**Reasoning — the WHAT & WHERE.** High-altitude, abstract, slow clock. Sets goals that span long horizons ("go to the park"), which it hands *down* to the predictive model to execute footstep-by-footstep. It is good at exactly what the predictive model is bad at (long horizons, abstraction) and bad at what the predictive model is good at (concrete continuous control). Quarantined: it generates and stress-tests candidate plans/goals only. It never scores and never decides. Treated as removable scaffolding — ideally reasoning is eventually just extended planning in the world model.

**Memory.** Two distinct stores:

- *Episodic memory:* specific past (situation → outcome) entries, retrieved by similarity to the current state, folded into perception and prediction. ("Last time I went down that path, I got hurt.")
- *Working buffer:* the handful of things alive during the current decision (candidates, scores, current state). Transient; clears each cycle.

(A third kind — the regularities baked into the models' weights — is not a store at all; it is the trained instinct of the models.)

**Decision layer — the courtroom.** Where standing wants meet imagined futures. For each candidate action it: takes the predicted future state from the world model, converts it (via a learned bridge) into a predicted *drive* state, scores that in drive currency plus an exploration/uncertainty-reduction term, with affect tuning the calculation. Collects one score per candidate, selects the winner, and emits **only the first action** before the loop runs again.

**Motor system.** Executes the first action. The world changes, the senses report it, the cycle repeats.

### Two things the diagram flattens

- **Habit shortcut.** The full loop above is the slow, deliberative path. Most behavior never travels it: once a routine has paid off against the drives enough times, it compiles into a fast path running nearly straight from perception to motor, skipping reasoning and most scoring. A mature agent is mostly habit with occasional deliberation. (Not in Phase 0; design interfaces so it can be added.)
- **Drives → reasoning link.** Candidate goals are generated *because they score well against the drives*. The diagram routes drives only to the decision layer for clarity, but the wanting is what makes any plan worth proposing in the first place.

---

## Data design

There are **two completely different representational regimes**, and they meet at the decision layer. Conflating them is the central design error to avoid.

| | Internal / drive state | External / world state |
|---|---|---|
| Shape | small, explicit, **named** struct you design | large, **learned** vector the model produces |
| Legible? | yes — inspect and debug constantly | no — mostly uninterpretable |
| Example | `{energy: 0.3, temperature: 0.6, social: 0.8}` | a fixed-length latent array |
| Who defines it | you | the world model (learned) |

Key rules that follow:

- **Drive state is stored data.** A plain object/struct with named float fields, updated each step.
- **Affect is a function over that data, not more fields in it.** It returns modulation parameters, recomputed each cycle.
- **World state is a separate learned representation.** The predictive model maps `(world_state, action) → predicted world_state` — same type in and out.
- **A learned bridge connects the two regimes:** `predicted world_state → predicted drive_state`. This is what lets "I'd be standing on the food tile" become "energy would rise." Without it, the opaque world representation and the legible drive representation cannot talk.
- **Value is a scalar** produced by the drive core's value function evaluated on a *predicted drive state*.
- **"Happiness" is not a stored field.** It is computed from how the drive state is trending. The agent never forecasts "I'll be happy"; it forecasts "energy up, threat down," and that positive trend *is* what the mood reflects. Storing happiness next to temperature recreates the mood-vs-need confusion.

Per-candidate-action pipeline:

```
current world_state + action
        --> predicted world_state          (predictive model)
        --> predicted drive_state           (learned bridge)
        --> scalar score                    (drive value fn, tuned by affect)
```

The decision layer runs this for each candidate and picks the highest score, then emits that candidate's first action.

---

## Roadmap

Each phase isolates one source of error before building on it. **Do not start a phase until the previous one is validated by watching it work.**

- **Phase 0 — drives in a gridworld (current).** Validate that the drive core alone produces coherent behavior in a trivial, fully-known world. No learning, no neural networks, no world model. *(Detailed below.)*
- **Phase 1 — minimal learning loop.** Add a simple learned policy / value estimate in the same gridworld; confirm nonlinear drive prioritization emerges from experience rather than being hand-coded.
- **Phase 2 — predictive world model + emergent affect.** Move to a richer 3D simulator. Add the predictive hierarchy and the affect modulation layer; test for fear-like / curiosity-like regimes arising from drive patterns under perturbation.
- **Phase 3 — multimodal sensorimotor fusion.** Add additional senses with asymmetric routing (chemoception → affective/interoceptive; vision/haptics → spatial world model). Learned world-state representation comes online.
- **Phase 4 — multi-agent & social drives.** Introduce other agents; test emergent social behavior from a cohesion drive.
- **Phase 5 — physical embodiment.** Sim-to-real transfer. Highest-risk phase; deferred deliberately.

The single highest-risk assumption in the whole project is the **choice and parameterization of the drives**. Everything is downstream of it, so it gets disproportionate scrutiny before the architecture calcifies around it.

---

## Phase 0 — the only thing being built now

### Goal

Show that an agent with a hand-written drive core, in a trivial gridworld, **balances feeding itself against exploring**, and **prioritizes food more sharply as energy gets critically low** — without any of that behavior being explicitly scripted.

### Environment

A small 2D gridworld:

- The agent occupies a cell and can move in the four cardinal directions.
- `energy` decays a fixed amount each step.
- Food tiles restore energy when entered.
- (Optional) a hazard tile that is costly to enter.
- The world is fully known and fully observable — so in Phase 0 the "world state" is a clean explicit object (agent position, food positions), *not* a learned vector.

### Drives (specify as actual math, not prose)

Start with two:

- **Energy** — a deficit drive. Setpoint, and reward defined as the *reduction in distance* from that setpoint. Urgency must grow nonlinearly as energy approaches critical, so a near-empty energy drive dominates a nearly-full one automatically (no hand-tuned weights).
- **Curiosity / exploration** — an open-ended drive. Rewards visiting unfamiliar states; has no satiation level.

Write down, explicitly: each setpoint, how urgency scales with distance from setpoint, and how the two drives combine into a single scalar value.

### Decision rule

Trivial for now: evaluate the candidate actions one step ahead, score each by the combined drive value function, pick the best. No learning yet. (This is the decision layer in its simplest possible form; learning arrives in Phase 1.)

### What is explicitly NOT in Phase 0

No world model (the gridworld is known), no reasoning module, no affect layer, no neural networks, no episodic memory, no habit shortcut. These are stubbed or absent. The point is to validate the drives in isolation.

### Definition of done

A runnable experiment (not just the agent) that produces a plot or metrics showing:

1. the agent reliably keeps energy above critical by seeking food, and
2. the sharpness of its food-seeking scales with how low energy is, and
3. when energy is comfortable, the exploration drive keeps it moving rather than idle.

If this holds, Phase 0 is validated and Phase 1 may begin. If it doesn't, the drives are wrong — and finding that out in ~50 lines of code is the most valuable thing this phase can do.

---

## Repository structure

The repo mirrors the architecture's boxes so it can grow phase by phase. Boxes not yet built are stubs with defined interfaces, so they can be filled in one at a time without rewiring.

```
drives/         # the drive core — written and verified by hand
environment/    # the world the agent lives in (gridworld now; swappable later)
world_model/    # stub in Phase 0 (world is known); learned predictor later
decision/       # the arbitration / scoring layer
affect/         # stub in Phase 0; modulation function later
memory/         # stub in Phase 0; episodic store + working buffer later
agent/          # wires the boxes together; runs the perceive-score-act loop
experiments/    # the measurement harness — runs the agent, produces the plots
```

Design principle: even though Phase 0's world state is a plain object, the **interfaces are written as if it were opaque**, so the gridworld and a future learned world model present the same contract to the decision layer. Swap one for the other later without touching the decision layer.

### Working with a coding agent

A coding agent should be pointed at this README's Phase 0 section as the source of truth — *not* at the architecture diagram, which describes roles, not an implementation. Have it scaffold the structure above, implement the environment and drives exactly as specified, write the trivial decision rule and the loop, and — crucially — write the measurement harness that tests the "definition of done."

Review the `drives/` module by hand regardless of who writes the rest. Reasonable-looking-but-subtly-wrong drives produce an agent that competently pursues the wrong things, and that error stays invisible until much later. Everything else in the early repo is plumbing the agent can own; the drives are yours to verify.