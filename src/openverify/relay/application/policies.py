"""Policy stages use the same provider invocation boundary as graph operations."""

import hashlib
from collections.abc import Callable
from typing import cast

from openverify.dataflow import resolve_inputs
from openverify.errors import ProtocolError
from openverify.fingerprint import fingerprint
from openverify.model import (
    Activation,
    Admission,
    AdmissionPolicy,
    Capability,
    Context,
    PolicyEvaluation,
    Selection,
    VerificationDefinition,
)
from openverify.policy import ROLES, check_outcome, policies
from openverify.relay.application.contract import validate_report
from openverify.relay.application.execution import invocation
from openverify.relay.ports import (
    AvailableProvider,
    ExecutionDriver,
    InvocationReport,
    InvocationRequest,
)
from openverify.validation import parse_object


async def evaluate_policies(
    definition: VerificationDefinition,
    values: Context,
    opportunity_id: str,
    providers: dict[str, AvailableProvider],
    driver: ExecutionDriver,
    timeout: float,
    audit: Callable[[str, InvocationRequest, InvocationReport | None], None],
) -> list[PolicyEvaluation] | None:
    evaluations: list[PolicyEvaluation] = []
    for role, policy in zip(ROLES, policies(definition), strict=True):
        inputs, resolutions, blocked = resolve_inputs(policy, values, {}, definition.graph)
        if blocked:
            raise ProtocolError("POLICY_INPUT", f"Unavailable {role} input")
        executor_ref = executor_version = None
        if policy.operation is not None:
            provider = providers[role]
            request = invocation(
                provider,
                policy.operation.capability_id,
                policy.operation.capability_version,
                inputs,
                policy.config,
            )
            audit(f"policy:{role}", request, None)
            report = await driver.execute(provider, request, timeout, lambda _: None)
            report = validate_report(request, report)
            audit(f"policy:{role}", request, report)
            if (
                report.error
                or report.output_error
                or report.outcome is None
                or report.outcome.state != "COMPLETED"
            ):
                raise ProtocolError(
                    "POLICY_OUTPUT", f"{role} provider did not complete successfully"
                )
            outcome = cast(
                Activation | Selection | Admission,
                parse_object(role.lower(), report.outcome.output),
            )
            executor_ref = provider.manifest.provider_id
            executor_version = provider.manifest.provider_version
        elif (
            isinstance(policy, Capability)
            and role == "ACTIVATION"
            and policy.executor_ref == "MANUAL"
        ):
            outcome = Activation(outcome="ACTIVATE", reason="Host invocation")
        elif (
            isinstance(policy, Capability)
            and role == "SELECTION"
            and policy.executor_ref == "EXPLICIT"
        ):
            outcome = Selection(subjects=[definition.subject], reason="Explicit subject")
        elif isinstance(policy, AdmissionPolicy) and policy.strategy in ("ALWAYS", "PROBABILITY"):
            p = 1.0 if policy.strategy == "ALWAYS" else cast(float, policy.probability)
            key = f"{fingerprint(definition)}\0{definition.subject.id}\0{opportunity_id}".encode()
            bucket = int.from_bytes(hashlib.sha256(key).digest(), "big")
            admit = p == 1 or (p != 0 and bucket < p * (1 << 256))
            outcome = Admission(
                outcome="RUN" if admit else "SKIP",
                reason="ALWAYS" if policy.strategy == "ALWAYS" else "Deterministic probability",
            )
        else:
            raise ProtocolError("POLICY_UNSUPPORTED", f"Unsupported built-in {role} policy")
        check_outcome(role, outcome, definition)
        evaluations.append(
            PolicyEvaluation.model_validate(
                dict(
                    role=role,
                    input_values=inputs,
                    input_resolutions=resolutions,
                    outcome=outcome,
                    executor_ref=executor_ref,
                    executor_version=executor_version,
                )
            )
        )
        if isinstance(outcome, Activation) and outcome.outcome == "DO_NOT_ACTIVATE":
            return None
        if isinstance(outcome, Selection) and not outcome.subjects:
            return None
    return evaluations
