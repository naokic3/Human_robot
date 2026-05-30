# Roadmap — Drive-Based Embodied Agent

This is the *how* behind the project. The README states the architecture; this document states the order of construction and, for each phase, what to build, what to borrow, what to watch out for, and the gate that must be passed before moving on.

## The one rule that governs everything

**Each phase isolates a single source of error and validates it before the next phase builds on it.** You do not advance because a phase is "mostly working" or because the next phase is more exciting. You advance only when the phase's gate is met and you have *watched it work*. The entire reason for phasing is that this system is a stack of dependencies — a flaw in an early layer doesn't announce itself; it quietly corrupts everything above it. The drives are the deepest layer, so they get the most scrutiny and the least tolerance for "good enough."

A corollary: the impressive parts (3D worlds, learned world models, embodiment) are deliberately last. The temptation at every stage is to skip ahead to them. Resist it. A validated gridworld is worth more than an unvalidated humanoid.

---

## Phase 0 — Drives in a gridworld

**Purpose.** Prove that a hand-written drive core, with no learning and no world model, produces coherent need-balancing behavior in a trivial, fully-known world. This is the cheapest possible test of the project's single highest-risk assumption: the drives themselves.

**What you build.**
- A small 2D gridworld: an agent that moves in four directions; an `energy` level that decays each step; food tiles that restore it; optionally a hazard tile.
- The world is fully observable and fully known, so the "world state" is a plain explicit object (positions), *not* a learned representation. You are deliberately cheating on perception here so that nothing distracts from the drives.
- Two drives, written as actual math:
  - **Energy** (deficit): a setpoint, with reward defined as the *reduction in distance* from setpoint, and urgency that grows *nonlinearly* as energy approaches critical — so a near-empty drive dominates a near-full one without hand-tuned weights.
  - **Curiosity** (open-ended): rewards visiting unfamiliar states; never satiates.
- A trivial decision rule: look one step ahead at each candidate move, score it with the combined drive value, pick the best. No learning.
- A **measurement harness** — the actual deliverable. Something that runs the agent and produces plots/metrics.

**What you borrow.** Nothing. This is ~50–150 lines you write and understand completely.

**Failure modes to watch.**
- Drives that produce a "grim" agent that goes inert the moment energy is comfortable — means your open-ended drive is too weak or mis-shaped.
- An agent that walks off into the hazard while starving — means urgency isn't scaling nonlinearly; the energy drive should dominate near-critical.
- Subtly wrong drive math that *looks* fine — this is the dangerous one. Read the drive code by hand, line by line, regardless of who wrote it.

**Gate (may not proceed until all hold).**
1. The agent reliably keeps energy above critical by seeking food.
2. The sharpness of food-seeking scales with how low energy is.
3. When energy is comfortable, curiosity keeps the agent exploring rather than idle.

If these don't hold, the drives are wrong — and discovering that in 50 lines is the most valuable thing this phase can do.

---

## Phase 1 — A learning loop in the same world

**Purpose.** Replace the hand-coded one-step decision rule with *learning*, while staying in the safe, legible gridworld. Confirm that drive-balancing behavior survives — and ideally improves — when the agent learns from experience rather than being told what to do each step. This is the first time the agent gets better over time.

**What you build.**
- A learned value/policy component that, instead of one-step lookahead, learns from experience which actions lead to drive satisfaction over a longer horizon. (A standard model-free RL method is fine here — the point is not sophistication, it's confirming that learning driven by the drive-derived reward produces sensible behavior.)
- Keep the same gridworld and the same two drives. Change *only* the decision mechanism. One variable at a time.
- Extend the harness to show learning curves, not just snapshots.

**What you borrow.** A standard RL implementation/library for the learning algorithm. The *reward* is not borrowed — it comes from your drive core (reduction in drive-distance). This is the critical seam: the agent learns, but what it learns to want still comes entirely from the drives.

**Failure modes to watch.**
- Reward shaping creeping in — if you find yourself adding bonuses to "help" the agent learn faster, stop. Those bonuses are exogenous goals sneaking back in. The reward must stay purely drive-derived.
- The agent learning a degenerate exploit of your drive math (e.g. oscillating to farm the curiosity reward). This is informative: it means the drive is exploitable and needs reshaping. Fix the drive, not the agent.

**Gate.**
1. The learned agent matches or beats the Phase-0 hand-coded agent on the same three behaviors.
2. Behavior improves measurably with experience.
3. No reward shaping was needed — the drive-derived reward alone was sufficient.

---

## Phase 2 — Predictive world model + emergent affect

**Purpose.** This is the project's steepest cliff and its longest phase. Two big additions: (a) the agent moves to a real 3D simulator with senses it can't be handed cleanly, forcing a *learned* world model; (b) the affect layer comes online, and you test whether emotion-like regimes emerge from drive patterns. Budget months, not weeks.

**What you build / borrow — keep these straight, they are different things:**

- **The simulator (borrow outright, never build).** Pick one: MuJoCo (physics-based control, the research standard, free), Isaac Sim/Lab (GPU-accelerated, parallel sims, photorealistic — heavier), or Habitat (indoor 3D navigation for embodied agents). Choice depends on the agent's body and world. This is the agent's *external reality*. You learn its interface; you do not write a physics engine.

- **The world model (borrow the architecture, train it yourself).** This is the agent's *internal, learned, imperfect imagination of* the simulator — a different thing from the simulator itself. Take a released architecture from the Dreamer lineage (latent world model + planning in imagination) or the JEPA lineage (predict in abstract representation space). You do **not** download a finished model and plug it in — a world model is *of a specific world*, so you train it from scratch inside your chosen simulator, on your agent's own experience. Borrowed: the network design and training machinery. Homegrown: the actual learned model.
  - The one place even the borrowed architecture must be modified is the **drive-coupling seam**: a standard world model predicts the world neutrally for an external reward; yours must feed predictions through the bridge into drive-currency. Expect to spend real time just getting a borrowed world model to *train stably* in your simulator **before** you attach it to your drives. Do that stabilization as its own sub-step.

- **The affect layer (build yourself).** A function over the drive state and recent prediction-error statistics that returns modulation parameters (planning horizon, caution, exploration weight). Not stored state — recomputed each cycle. This is where you test the project's most interesting claim.

**Sub-sequence within Phase 2 (don't do these at once):**
1. Stand up the simulator with a simple body and your drives; get the Phase-1-style learning working there with a *trivial* world model first.
2. Swap in the real learned world model; get it training stably; confirm planning-in-imagination works.
3. Attach the world model to the drives via the bridge.
4. Only then add the affect layer.

**Failure modes to watch.**
- Sim-to-real anxiety leaking in early — ignore real hardware entirely this phase.
- The world model dominating: if it predicts beautifully but the agent behaves worse, the drive-coupling seam is wrong.
- Treating affect as stored fields (a "happiness" variable) instead of a computed function — recreates the mood-vs-need confusion. Affect is code that runs on the drive state.
- Sample-efficiency pain: real trials in a 3D sim are far costlier than gridworld steps. This is where the "learn mostly in imagination" payoff matters; if you're not learning in the world model's rollouts, you'll be too slow.

**Gate.**
1. The agent maintains its drives in the 3D world, learning largely from imagined rollouts rather than brute real trials.
2. Under perturbation (threaten a drive), the affect layer produces a *functionally distinct regime* — e.g. a fear-like mode: shortened horizon, raised threat-precision, suppressed exploration — that you did not script.
3. You can point to a behavior and trace it back through affect → drive pattern → architecture, rather than to a hand-coded rule.

---

## Phase 3 — Multimodal sensorimotor fusion

**Purpose.** Give the agent more than one sense, fused correctly. The key insight is *asymmetric routing*: not all senses feed the same place.

**What you build.**
- Additional sensory channels in the simulator. Route them by their nature, mirroring biology:
  - Vision and haptics → the spatial world model (high-bandwidth, spatially rich).
  - Chemoception-like signals (low-dimensional, valence-laden) → the affective/interoceptive side, *not* the spatial world model. These connect to drives more naturally than to the spatial map.
- The world model now builds a genuine learned world-state representation fusing the spatial senses, because the agent can no longer be handed clean state.
- Object-centric / structured state representation if multi-entity reasoning is needed (sets up Phase 4).

**What you borrow.** Representation-learning components (object-centric / slot-based encoders, multimodal fusion architectures) — adapted, trained in your sim.

**Failure modes to watch.**
- Late-concatenation fusion (separate pipelines glued at the end) — the wrong default. Fusion should happen because modalities share a common predicted cause, not because you stapled vectors together.
- Forcing low-dimensional senses (smell/taste analogs) into the spatial model. Keep the asymmetric routing.

**Gate.**
1. The agent integrates multiple senses into a coherent world-state, demonstrated by behavior that requires cross-modal binding (acting correctly on something seen *and* felt).
2. Valence-laden low-bandwidth senses demonstrably influence affect/drives rather than the spatial map.

---

## Phase 4 — Multi-agent and social drives

**Purpose.** Introduce other agents and a hardcoded social-cohesion drive, and test whether social behavior — attachment, social referencing, proto-empathy — *emerges* rather than being scripted. This is also where long-term goals / standing commitments become relevant.

**What you build.**
- Other agents in the environment (initially copies of the system, later humans).
- A social-cohesion drive (and possibly a separation-distress / care pair), grounded the same way as every other drive: it spikes when the relevant social variable leaves its range.
- Modeling other agents' states inside the world model — because predicting another's state now predicts your own social-drive satisfaction. This is the mechanical basis for proto-empathy.
- The **value-source layering** discussed for long-term goals: standing commitments (grounded in drives) join the drives as persistent value sources; an arbiter scores candidate goals against all value sources; an execution stack runs the chosen one and is interruptible when a drive spikes.

**What you borrow.** Multi-agent simulation tooling; developmental-robotics ideas for social learning.

**Failure modes to watch.**
- Scripting social behavior directly — defeats the point. Social behavior must fall out of the cohesion drive plus modeling others.
- Long-term goals drifting free of drives. **The grounding rule:** every standing commitment must trace to a drive it serves. If you can't name the drive a long-term goal serves, that goal shouldn't exist in the agent. This is what keeps the multi-timescale goal machinery from becoming a parallel, exogenous source of purpose.

**Gate.**
1. Social behaviors (approach, attachment, referencing) appear without being explicitly programmed.
2. The agent adopts and pursues at least one long-term, drive-grounded commitment across many interrupted sessions, correctly deprioritizing it when immediate drives spike.

---

## Phase 5 — Physical embodiment

**Purpose.** Move from simulation to a physical body. Deferred to last deliberately — this is the graveyard of embodied-AI projects.

**What you build / borrow.**
- A physical platform (borrow — do not build a robot from scratch unless that is itself your research).
- Sim-to-real transfer: domain randomization, careful calibration, and the expectation that things that worked in sim will fail on hardware until the gap is closed.
- Possibly neuromorphic hardware (Loihi, SpiNNaker) *only if* real-time, low-power, event-driven processing becomes a binding constraint — an optional later track, high engineering risk, not a default.

**Failure modes to watch.**
- The sim-to-real gap: unmodeled friction, sensor noise, latency, contact dynamics. Budget heavily for this; it is the whole difficulty of the phase.
- Discovering only now that a drive was mis-specified — which is why every earlier phase guarded the drives so jealously.

**Gate.**
1. The agent maintains its drives and exhibits its learned behavioral repertoire on physical hardware.
2. Affective regimes and social behaviors transfer, not just low-level control.

---

## A note on the hard problem

Nothing in this roadmap delivers *phenomenal* consciousness, and there is no known way to verify it if it did. What this builds is a system whose *functional organization* — affect downstream of homeostasis, action downstream of affect — mirrors leading theories of how biological minds are organized. Frame the deliverable as that functional architecture and stay agnostic on the hard problem. It keeps the science honest and the claims defensible.

## The thing to keep returning to

At every phase, the question is the same: *is this still downstream of the drives?* The simulator, the world model, the senses, the social machinery, the long-term goals — all of it is borrowed or built infrastructure in service of needs the agent was given at the start. The moment any component starts generating its own purposes — a reward shaping that smuggles in goals, a reasoning module that decides what's worth wanting, a long-term goal with no drive beneath it — the project has quietly become something else. The drives are the root. Everything else is how the root reaches the world.
