"""SDK validation remains mandatory when a host replaces the physical driver."""

from openverify.model import ExecutionError
from openverify.provider import LifecycleValidator, ProviderContractError, wire_data
from openverify.relay.ports import InvocationReport, InvocationRequest


def validate_report(request: InvocationRequest, report: InvocationReport) -> InvocationReport:
    lifecycle = LifecycleValidator(request.manifest)
    lifecycle.initialize(
        {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]}
    )
    lifecycle.accept(wire_data(request.invocation))
    for event in report.events:
        lifecycle.event(wire_data(event))
    if report.outcome is not None:
        try:
            lifecycle.outcome(wire_data(report.outcome))
        except ProviderContractError as exc:
            if exc.code != "INVALID_PROVIDER_OUTPUT" or report.outcome.state != "COMPLETED":
                raise
            return InvocationReport(
                report.outcome,
                report.events,
                report.error,
                ExecutionError(code=exc.code, message=exc.message),
            )
        lifecycle.finish()
        if report.output_error is not None:
            raise ProviderContractError(
                "PROTOCOL_VIOLATION", "Driver claimed an unreproducible output-schema rejection"
            )
    elif report.error is None:
        raise ProviderContractError(
            "PROTOCOL_VIOLATION", "Driver returned neither outcome nor transport error"
        )
    return report
