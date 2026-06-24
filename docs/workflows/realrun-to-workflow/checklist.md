# checklist: realrun-to-workflow

## Promote To Workflow Only If

- [ ] There is real-run evidence.
- [ ] Manager can call it with `调用 workflow: <workflow_id>`.
- [ ] It involves a repeatable multi-agent collaboration boundary.
- [ ] It has a clear done definition.
- [ ] It has at least one acceptance gate.
- [ ] It has forbidden moves.
- [ ] It is not already covered by an existing workflow.

## Builder Output Must Include

- [ ] workflow_id
- [ ] when_to_use
- [ ] trigger_examples
- [ ] participants
- [ ] handoff_chain
- [ ] required_inputs
- [ ] expected_outputs
- [ ] acceptance_gates
- [ ] forbidden_moves
- [ ] reassurance_policy
- [ ] done_definition
- [ ] common_failure_modes
- [ ] registry update recommendation

## Block Closeout If

- The output is only a summary.
- No real evidence is cited.
- The workflow is too specific to one task prompt.
- The owner is unclear.
- It creates overlap with an existing workflow without explaining why.

