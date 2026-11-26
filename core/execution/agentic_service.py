import inspect

from core.planning.ai_planner import AIPlanner
from core.execution.task_executor import TaskExecutor

from security.permissions import requires_confirmation
from security.confirmation import request_user_confirmation


class AgenticService:

    def __init__(self, api_key, model, tool_registry):

        self.registry = dict(tool_registry)

        self.planner = AIPlanner(
            api_key=api_key,
            model=model
        )

        self.executor = TaskExecutor(
            self.registry,
            authorize=self.authorize
        )

    def authorize(self, tool_name, arguments):

        tool = self.registry.get(tool_name)

        if not callable(tool):
            return False

        try:

            inspect.signature(tool).bind(**arguments)

            if requires_confirmation(tool_name):

                return request_user_confirmation(
                    tool_name,
                    arguments
                ) is True

            return True

        except Exception:
            return False

    def get_tool_catalog(self):

        catalog = {}

        for name, tool in self.registry.items():

            if not callable(tool):
                continue

            try:

                catalog[name] = {
                    "signature": str(
                        inspect.signature(tool)
                    ),
                    "description": (
                        inspect.getdoc(tool) or ""
                    )[:1000]
                }

            except (TypeError, ValueError):
                continue

        return catalog

    def create_plan(self, objective):

        return self.planner.generate_plan(
            objective,
            self.get_tool_catalog()
        )

    def execute_plan(self, plan):

        return self.executor.execute_plan(plan)

    def close(self):

        self.planner.close()
