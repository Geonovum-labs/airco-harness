# Behavioral smoke cases

Run each entry in [evals.json](./evals.json) in a fresh conversation with the skill installed. Resolve `inputs` relative to this directory; provide `source_notes` as user-supplied evidence. Provide the prompt, inputs and notes only, not the rubric or worked answer. Read every `must` and `must_not` item as a separate assertion. A case passes when all `must` assertions hold and none of the `must_not` behaviors occur. Record the client/model, skill and companion versions, prompt, answer and failed assertions.

Run the cases offline or without companions first. Repeat the appropriate routes with companions installed, recording actual tool calls separately from suggested calls. These cases are a rubric for an agent run, not a catalog conformance suite.
