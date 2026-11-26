from core.planning.task_plan import TaskStatus
from core.monitoring.performance import performance_monitor


class TaskExecutor:

    def __init__(self, tool_registry, authorize=None):

        self.tool_registry = dict(tool_registry)
        self.authorize = authorize

    def execute_step(self, step):

        if step.status != TaskStatus.PENDING:
            return

        tool = self.tool_registry.get(step.tool_name)

        if not callable(tool):

            step.status = TaskStatus.FAILED
            step.result = {
                "success": False,
                "message": "Tool not registered."
            }

            return

        try:

            approved = (
                self.authorize is not None
                and self.authorize(
                    step.tool_name,
                    step.arguments
                ) is True
            )

        except Exception:
            approved = False

        if not approved:

            step.status = TaskStatus.BLOCKED
            step.result = {
                "success": False,
                "message": "Authorization denied."
            }

            return

        step.status = TaskStatus.RUNNING

        try:

            with performance_monitor.measure(
                step.tool_name
            ):

                result = tool(**step.arguments)

                step.result = result

                if (
                    isinstance(result, dict)
                    and result.get("success") is True
                ):

                    step.status = TaskStatus.COMPLETED

                else:

                    step.status = TaskStatus.FAILED

                    raise RuntimeError(
                        "Tool success was not verified."
                    )

        except Exception:

            step.status = TaskStatus.FAILED

            if step.result is None:

                step.result = {
                    "success": False,
                    "message": "Task execution failed."
                }

    def execute_plan(self, plan):

        while True:

            ready_steps = plan.get_ready_steps()

            if not ready_steps:
                break

            for step in ready_steps:
                self.execute_step(step)

        for step in plan.steps:

            if step.status == TaskStatus.PENDING:

                step.status = TaskStatus.BLOCKED

                step.result = {
                    "success": False,
                    "message": "Dependency not completed."
                }

        return plan.to_dict()
