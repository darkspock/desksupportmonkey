class WorkflowTemplateNotFoundError(Exception):
    def __init__(self, template_id: str) -> None:
        super().__init__(f"Workflow template not found: {template_id}")
        self.template_id = template_id


class DuplicateTemplateNameError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"A workflow template with name '{name}' already exists")
        self.name = name


class TemplateHasRequestsError(Exception):
    def __init__(self, template_id: str) -> None:
        super().__init__(
            f"Cannot delete template '{template_id}': it has associated requests"
        )
        self.template_id = template_id
