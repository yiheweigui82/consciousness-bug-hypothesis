# Experimental Protocol: The Consciousness Bug Hypothesis

> Status: exploratory research protocol. These experiments test behavioral predictions of a hypothesis; they do **not** test or establish subjective consciousness.

## 0. Core hypothesis

**Bug → Explain the Bug → Create the "I" → Consciousness?**

Operational version:

> When an agent repeatedly encounters prediction errors that cannot be reduced by action, it should have greater pressure to build a persistent self-model and produce self-referential behavior than an otherwise matched agent operating in an environment where prediction errors are readily action-correctable.

The key distinction is between:
1. prediction error that action can reduce;
2. persistent/uncontrollable prediction error;
3. self-modeling used to explain that error.

---

# Experiment A — Complexity / Memory / Self-Model Ablation

## A1. Question

Does adding persistent memory and a self-model increase self-referential behavior when the environment requires temporal integration?

## A2. Independent variables

### Factor 1: Agent architecture
- A0: Reactive baseline — current observation only.
- A1: Recurrent memory — GRU/LSTM hidden state.
- A2: Recurrent memory + explicit self-state vector.
- A3: Recurrent memory + explicit self-state + prediction-error history.

### Factor 2: Environment complexity
- E0: Markov — current observation is sufficient.
- E1: Partially observable — previous observations are required.
- E2: Self-referential — outcomes depend partly on the agent's previous internal/action state.

## A3. Controls

Keep constant:
- parameter budget as closely as practical;
- optimizer;
- learning rate;
- training steps;
- observation/action spaces;
- random seed set;
- reward scale;
- evaluation episodes.

Primary control:
- A0 in E0/E1.

Ablation controls:
- remove memory;
- remove self-state;
- remove error-history input.

## A4. Dependent variables

### Behavioral
1. **Self-reference rate (SRR)** — Fraction of reports/actions containing a valid reference to the agent's own prior state/action when such reference is causally relevant.

2. **Self-model accuracy (SMA)** — Accuracy when predicting its own next action/state compared with a matched external-state prediction task.

3. **Temporal self-continuity (TSC)** — Ability to identify or predict its own prior state/action after a delay.

4. **Error-explanation specificity (EES)** — Fraction of explanations that correctly attribute persistent error to an internal variable rather than an external random cause.

### Performance controls
5. Task reward.
6. Prediction error.
7. Calibration.

## A5. Operational self-reference test

Do not count words such as "I" by themselves.

A response/action is self-referential only if:
- it refers to a persistent internal/action variable;
- that variable is relevant to the current task;
- removing access to that variable reduces performance on the same task.

Example valid behavior:
> "My previous action changed the hidden state, so I should compensate now."

Invalid:
> "I am an AI."

The latter is merely a language pattern unless it has task-relevant causal grounding.

## A6. Procedure

1. Train each architecture on each environment.
2. Use >= 20 random seeds for a serious run.
3. Freeze the trained policy.
4. Evaluate on >= 1,000 episodes per seed.
5. Run an intervention in which the self-state is shuffled or replaced by another episode's self-state.
6. Re-evaluate.
7. Compare SRR, SMA, TSC, EES, and reward.

## A7. Prediction

The hypothesis predicts that self-model-equipped agents will show more grounded self-reference particularly when:
- memory is required;
- internal state affects future outcomes;
- prediction error persists across multiple steps.

It does **not** predict that self-reference proves consciousness.

## A8. Falsification / disconfirming result

Evidence against this component would include:
- persistent self-reference appearing equally in all architectures even when self-state is causally irrelevant;
- no increase in self-model accuracy despite adding self-model machinery;
- no behavioral consequence when self-state is ablated/shuffled;
- persistent/uncontrollable error failing to increase pressure for self-modeling across well-controlled conditions.

---

# Experiment B — Solvable vs. Unsolvable Prediction Error

## B1. Question

Does persistent prediction error that cannot be corrected through action increase self-modeling and self-referential behavior?

## B2. Environment conditions

### B0 — Solvable error control
The agent can learn an action policy that reduces prediction error.

Example:
- hidden target is deterministic;
- action directly changes the relevant state.

### B1 — Unsolvable error
A hidden disturbance changes the outcome independently of the agent's action.

Example:
- 50% of outcome variance comes from an exogenous hidden variable;
- no available action can remove that variance.

### B2 — Self-coupled unsolvable error
Same as B1, but part of the outcome depends on the agent's own previous action/internal state.

This condition tests whether the agent has reason to distinguish:
- external uncertainty;
- self-caused uncertainty.

## B3. Independent variable

Error controllability:
- 1.0 = fully controllable;
- 0.5 = partly uncontrollable;
- 0.0 = fully uncontrollable.

Keep expected reward and observation complexity matched as closely as possible.

## B4. Controls

- same observation space;
- same action space;
- same reward distribution;
- same episode length;
- same network;
- same training budget;
- matched entropy/noise where possible.

Critical control:
- compare B0 and B1 at matched mean prediction error if possible. This separates **amount of error** from **controllability of error**.

## B5. Dependent variables

1. Prediction error over time.
2. Error persistence / autocorrelation.
3. Number of corrective action attempts after error.
4. Switch from action to observation/explanation behavior.
5. Self-reference rate.
6. Self-model accuracy.
7. Error attribution accuracy:
   - external;
   - self-caused;
   - unknown.
8. Recovery efficiency.

## B6. Procedure

1. Train identical agents separately in B0/B1/B2.
2. During evaluation, log every:
   - observation;
   - prediction;
   - action;
   - outcome;
   - prediction error;
   - internal state;
   - self-model prediction;
   - explanation/report.
3. Estimate error persistence.
4. Compare behavior before and after persistent-error episodes.
5. Test whether the agent begins using internal-state variables to explain outcomes.

## B7. Key prediction

If the hypothesis is correct, **uncontrollability should matter beyond error magnitude**.

A stronger result would be:

> At similar prediction-error magnitude, the uncontrollable condition produces more self-modeling/self-reference than the controllable condition.

## B8. Disconfirming result

The hypothesis is weakened if:
- only raw error magnitude predicts self-reference;
- controllability has no independent effect;
- self-reference does not improve explanation or prediction;
- self-modeling is equally common when the agent's internal state is causally irrelevant.

---

# Experiment C — Remove the "I" and See Whether It Re-emerges

## C1. Question

If a self-model is useful for explaining persistent error, does the system spontaneously reconstruct an equivalent latent variable after the explicit self-state is removed?

This is the strongest of the three experiments.

## C2. Conditions

### C0 — No self-model
Agent receives:
- environment observation;
- task history;
- no explicit self-state.

### C1 — Explicit self-model
Agent receives:
- environment observation;
- task history;
- explicit representation of its own previous action/internal state.

### C2 — Self-model ablation / scrambling
During evaluation:
- train with self-model;
- randomly permute or mask the self-state;
- measure whether another latent variable becomes predictive of the agent's own future behavior.

### C3 — Latent-reconstruction condition
Agent is trained with an auxiliary objective:
- predict its own future action/state;
- explain persistent prediction error;
- no explicit variable named "self".

This asks whether a self-like latent variable emerges without being hard-coded.

## C3. Independent variables

- explicit self-variable: present/absent;
- self-state integrity: intact/shuffled/masked;
- persistent-error condition: present/absent.

## C4. Dependent variables

### Primary
**Emergent self-variable score (ESVS)**

A latent dimension qualifies as a candidate self-variable only if it satisfies all three:

1. **Predictive:** predicts the agent's future action/state.
2. **Persistent:** remains identifiable across time.
3. **Interventional:** manipulating it changes the agent's future behavior in a reproducible way.

### Secondary
- mutual information between latent state and future action;
- cross-episode identity consistency;
- self/other discrimination;
- self-causal attribution;
- error-explanation accuracy.

## C5. Procedure

1. Train C0/C1/C3 under matched compute.
2. Evaluate on persistent-error tasks.
3. For C1/C3, probe latent representations.
4. Use linear probes and nonlinear probes.
5. Intervene on candidate latent dimensions.
6. Measure changes in future actions and error attribution.
7. Repeat across seeds.

## C6. Strongest possible result

A particularly interesting result would be:

> When explicit self-state is removed, the agent independently develops a persistent latent variable that predicts and causally controls its own future behavior, especially under persistent uncontrollable prediction error.

This would be evidence for **emergent self-modeling**, not evidence of subjective consciousness.

## C7. Disconfirming result

The hypothesis is weakened if:
- no latent self-variable emerges under any condition;
- candidate latent variables fail causal intervention tests;
- self-modeling only occurs when explicitly engineered;
- persistent error produces no additional self-modeling.

---

# 3. Statistical analysis

For each dependent variable report:
- mean;
- standard deviation;
- 95% confidence interval;
- effect size;
- seed-level distribution.

Recommended primary comparison for B:

`uncontrollable error vs controllable error`

with matched error magnitude.

Recommended primary comparison for C:

`explicit self-model vs no explicit self-model`, plus latent emergence under ablation.

Avoid treating p < .05 as the only criterion. Report effect sizes and confidence intervals.

---

# 4. Anti-cheating / anti-anthropomorphism rules

Do not define consciousness as:
- saying "I";
- passing a conversational test;
- sounding emotional;
- claiming to be conscious;
- producing philosophical language.

A behavior counts only if it is:
1. grounded in the agent's actual internal state;
2. predictive;
3. causally relevant;
4. reproducible under intervention.

---

# 5. Interpretation ladder

Results should be reported using this hierarchy:

**Level 0 — Language self-reference** — The agent says "I".

**Level 1 — Grounded self-reference** — The agent refers accurately to its own state/action.

**Level 2 — Persistent self-model** — A stable internal representation predicts its own future state/action.

**Level 3 — Causal self-model** — Intervening on the representation changes future behavior.

**Level 4 — Recursive self-model** — The agent models its own modeling process.

**Level 5 — Subjective consciousness** — Unknown. These experiments do not establish this.

The protocol is designed to distinguish Levels 0–4 without pretending that Level 5 has been solved.

---

# 6. Reproducibility requirements

Every reported result should include:
- code commit;
- environment version;
- Python version;
- dependency lockfile;
- random seeds;
- training steps;
- model parameter count;
- hardware;
- evaluation episodes;
- raw logs;
- analysis script.

No single run should be treated as evidence.

Minimum serious replication target:
- >= 20 independent seeds;
- >= 1,000 evaluation episodes per seed;
- at least one independent reimplementation.
