from drf_spectacular.openapi import AutoSchema


class ModuleTaggedAutoSchema(AutoSchema):
    """Group Swagger operations into readable module-based tags."""

    MODULE_TAGS = {
        "auth": "Authentication",
        "users": "Users",
        "organizations": "Organizations",
        "invites": "Invites",
        "projects": "Projects",
        "tasks": "Tasks",
        "comments": "Comments",
        "attachments": "Attachments",
        "notifications": "Notifications",
        "activity-logs": "Activity Logs",
        "webhooks": "Webhooks",
    }

    def get_tags(self):
        path_parts = [part for part in self.path.strip("/").split("/") if part]

        # Expected API path: /api/v1/<module>/...
        if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "v1":
            module_key = path_parts[2]

            # Split auth endpoints from user profile endpoints for cleaner docs.
            if module_key == "users" and len(path_parts) >= 4 and path_parts[3] == "auth":
                return ["Authentication"]

            return [self.MODULE_TAGS.get(module_key, module_key.replace("-", " ").title())]

        return super().get_tags()
