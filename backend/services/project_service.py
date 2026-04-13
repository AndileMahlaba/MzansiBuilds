from __future__ import annotations

from backend.constants import PROJECT_STAGES, PROJECT_ACTIVE
from backend.models.project import Project
from backend.models.user import User
from backend.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, projects: ProjectRepository | None = None) -> None:
        self._repo = projects or ProjectRepository()

    def create(
        self,
        owner: User,
        title: str,
        description: str,
        stage: str,
        support_needed: str,
    ) -> tuple[Project | None, str | None]:
        err = self._validate_stage(stage)
        if err:
            return None, err
        if not title or len(title.strip()) < 2:
            return None, "Please give the project a clearer title."
        p = self._repo.create(owner, title, description, stage, support_needed)
        return p, None

    def update(
        self,
        project: Project,
        actor: User,
        title: str | None,
        description: str | None,
        stage: str | None,
        support_needed: str | None,
    ) -> tuple[Project | None, str | None]:
        if project.user_id != actor.id:
            return None, "You can only edit your own projects."
        if stage is not None:
            err = self._validate_stage(stage)
            if err:
                return None, err
        p = self._repo.update(project, title, description, stage, support_needed)
        return p, None

    def complete(self, project: Project, actor: User) -> tuple[Project | None, str | None]:
        if project.user_id != actor.id:
            return None, "Only the owner can mark a project complete."
        if project.status != PROJECT_ACTIVE:
            return None, "This project is already finished."
        return self._repo.mark_completed(project), None

    def add_milestone(
        self, project: Project, actor: User, title: str, description: str
    ) -> tuple[object | None, str | None]:
        if project.user_id != actor.id:
            return None, "Only the owner can add milestones."
        if not title or len(title.strip()) < 2:
            return None, "Please add a short milestone title."
        m = self._repo.add_milestone(project.id, title, description)
        return m, None

    def add_comment(
        self, project: Project, actor: User, content: str
    ) -> tuple[object | None, str | None]:
        if not content or len(content.strip()) < 1:
            return None, "Comment cannot be empty."
        c = self._repo.add_comment(project.id, actor.id, content)
        return c, None

    def request_collaboration(
        self, project: Project, actor: User, message: str
    ) -> tuple[object | None, str | None]:
        if project.user_id == actor.id:
            return None, "You cannot collaborate on your own project through a request."
        if self._repo.get_pending_collaboration(project.id, actor.id):
            return None, "You already have a pending collaboration request for this project."
        r = self._repo.add_collaboration_request(project.id, actor.id, message)
        return r, None

    @staticmethod
    def _validate_stage(stage: str) -> str | None:
        s = stage.strip().lower()
        if s not in PROJECT_STAGES:
            return "Pick a valid stage for the project."
        return None


# I kept ownership and stage checks in this service because I had the same if-statements scattered
# across routes at first, and my tests kept failing whenever I updated one branch and forgot another.
# If you extend the project with more actions, add them here and keep the HTTP layer mostly dispatch.
