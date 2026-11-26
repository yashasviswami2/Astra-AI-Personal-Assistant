from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class TaskStatus(str, Enum):

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class TaskStep:

    description: str
    tool_name: str

    arguments: dict = field(default_factory=dict)
    dependencies: list = field(default_factory=list)

    step_id: str = field(
        default_factory=lambda: uuid4().hex
    )

    status: TaskStatus = TaskStatus.PENDING

    result: object = None


@dataclass
class TaskPlan:

    objective: str

    steps: list = field(default_factory=list)

    plan_id: str = field(
        default_factory=lambda: uuid4().hex
    )

    def add_step(
        self,
        description,
        tool_name,
        arguments=None,
        dependencies=None
    ):

        if len(self.steps) >= 12:
            raise ValueError("Maximum plan size exceeded.")

        dependencies = list(dependencies or [])

        existing_ids = {
            step.step_id for step in self.steps
        }

        if not set(dependencies).issubset(existing_ids):
            raise ValueError("Invalid task dependency.")

        step = TaskStep(
            description=description,
            tool_name=tool_name,
            arguments=dict(arguments or {}),
            dependencies=dependencies
        )

        self.steps.append(step)

        return step

    def get_progress(self):

        total = len(self.steps)

        completed = sum(
            step.status == TaskStatus.COMPLETED
            for step in self.steps
        )

        failed = sum(
            step.status == TaskStatus.FAILED
            for step in self.steps
        )

        blocked = sum(
            step.status == TaskStatus.BLOCKED
            for step in self.steps
        )

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "progress": round(
                completed / total * 100, 2
            ) if total else 0
        }

    def get_ready_steps(self):

        completed_ids = {
            step.step_id
            for step in self.steps
            if step.status == TaskStatus.COMPLETED
        }

        return [
            step
            for step in self.steps
            if step.status == TaskStatus.PENDING
            and all(
                dependency in completed_ids
                for dependency in step.dependencies
            )
        ]

    def to_dict(self):

        return {
            "plan_id": self.plan_id,
            "objective": self.objective,
            "progress": self.get_progress(),
            "steps": [
                {
                    "id": step.step_id,
                    "description": step.description,
                    "tool": step.tool_name,
                    "dependencies": step.dependencies,
                    "status": step.status.value
                }
                for step in self.steps
            ]
        }
