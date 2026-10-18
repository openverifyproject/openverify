"""Portable policy outcome/input invariants, independent of any policy executor."""

from openverify.dataflow import resolve_inputs
from openverify.errors import ProtocolError
from openverify.model import (
    Activation,
    Admission,
    AdmissionPolicy,
    Context,
    PolicyEvaluation,
    PolicyOperation,
    Selection,
    VerificationDefinition,
)
from openverify.serialization import json_equal, to_data

ROLES = ("ACTIVATION", "SELECTION", "ADMISSION")
OUTCOMES = {"ACTIVATION": Activation, "SELECTION": Selection, "ADMISSION": Admission}


def policies(definition: VerificationDefinition) -> list[PolicyOperation]:
    p = definition.execution_policy
    return [p.activation, p.selection, p.admission]


def check_outcome(
    role: str, outcome: Activation | Selection | Admission, definition: VerificationDefinition
) -> None:
    if type(outcome) is not OUTCOMES[role]:
        raise ProtocolError("POLICY_OUTPUT", "Policy outcome does not match role")
    if (
        isinstance(outcome, Selection)
        and outcome.subjects
        and not json_equal([to_data(s) for s in outcome.subjects], [to_data(definition.subject)])
    ):
        raise ProtocolError("POLICY_OUTPUT", "Selection must be empty or the definition subject")


def check_evaluations(
    definition: VerificationDefinition,
    values: Context,
    evaluations: list[PolicyEvaluation],
    admission: Admission,
) -> None:
    if len(evaluations) != 3:
        raise ProtocolError("PROVENANCE_LINEAGE", "Occurrence requires all policy evaluations")
    for role, policy, record in zip(ROLES, policies(definition), evaluations, strict=True):
        inputs, resolutions, blocked = resolve_inputs(policy, values, {}, definition.graph)
        check_outcome(role, record.outcome, definition)
        if (
            blocked
            or record.role != role
            or not json_equal(inputs, record.input_values)
            or not json_equal(
                {k: to_data(v) for k, v in resolutions.items()},
                {k: to_data(v) for k, v in record.input_resolutions.items()},
            )
        ):
            raise ProtocolError("PROVENANCE_LINEAGE", "Policy inputs/role contradict definition")
        if isinstance(policy, AdmissionPolicy) and isinstance(record.outcome, Admission):
            allowed = None
            if policy.strategy == "ALWAYS":
                allowed = {"RUN"}
            elif policy.strategy == "PROBABILITY":
                allowed = (
                    {"SKIP"}
                    if policy.probability == 0
                    else {"RUN"}
                    if policy.probability == 1
                    else {"RUN", "SKIP"}
                )
            if allowed is not None and record.outcome.outcome not in allowed:
                raise ProtocolError(
                    "PROVENANCE_LINEAGE", "Admission outcome contradicts built-in policy"
                )
    a, s, d = (e.outcome for e in evaluations)
    if (
        not isinstance(a, Activation)
        or a.outcome != "ACTIVATE"
        or not isinstance(s, Selection)
        or not s.subjects
        or not json_equal(to_data(d), to_data(admission))
    ):
        raise ProtocolError("PROVENANCE_LINEAGE", "Policy outcomes do not establish an occurrence")
