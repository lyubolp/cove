"""Routes for managing projects and user-project access."""

from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from cove.models.projects import Project, ProjectUserLink

from ..dependencies import get_session
from ..models.users import User
from ..services.auth.api_keys import api_key_header, does_api_key_grant_access_to_project
from ..services.auth.oauth2 import get_current_user, get_current_user_non_fatal, get_current_user_with_project_access

router = APIRouter(prefix="/project")


@router.get("/")
async def get_all_projects(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
) -> Sequence[Project]:
    """Return all projects visible to the caller.

    Always includes every public project. Private projects are included only when
    the caller is authenticated and holds a ``ProjectUserLink`` for them, or when
    the supplied API key grants access.
    """
    statement = select(Project)
    results = session.exec(statement)

    projects = results.all()

    public_projects = [project for project in projects if project.is_public]

    private_projects_with_access = []

    if current_user is not None:
        project_under_user_statement = select(ProjectUserLink).where(ProjectUserLink.user_id == current_user.id)
        user_links = session.exec(project_under_user_statement).all()

        for user_link in user_links:
            statement = select(Project).where(Project.id == user_link.project_id)
            project = session.exec(statement).first()

            if project and not project.is_public:
                private_projects_with_access.append(project)
    elif api_key is not None:
        for project in projects:
            if not project.is_public and does_api_key_grant_access_to_project(session, api_key, project.id):
                private_projects_with_access.append(project)

    return public_projects + private_projects_with_access


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
    api_key: Annotated[str | None, Depends(api_key_header)],
) -> Project | dict[str, str]:
    """Return a single project by id.

    Returns an error payload when the project does not exist or the caller lacks
    access to a private project.
    """
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project is None:
        return {"error": "Project not found"}

    if project.is_public:
        return project

    if current_user is not None:
        project_under_user_statement = select(ProjectUserLink).where(
            ProjectUserLink.user_id == current_user.id,
            ProjectUserLink.project_id == project.id,
        )
        user_link = session.exec(project_under_user_statement).first()

        if user_link:
            return project
    elif api_key is not None and does_api_key_grant_access_to_project(session, api_key, project.id):
        return project

    return {"error": "Project not found"}


@router.post("/{name}")
async def create_project(
    name: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Create a new private project owned by the authenticated user.

    A ``ProjectUserLink`` is automatically created so the creator has access.
    Returns the new project's id in the response payload.
    """
    project = Project(name=name, is_public=False)

    session.add(project)

    user_link = ProjectUserLink(project_id=project.id, user_id=current_user.id)
    session.add(user_link)
    session.commit()
    session.refresh(project)

    return {"status": "OK", "project_id": project.id}


@router.patch("/{project_id}", dependencies=[Depends(get_current_user_with_project_access)])
async def update_project(
    project_id: str,
    session: Annotated[Session, Depends(get_session)],
    name: str | None = None,
    is_public: bool | None = None,
) -> dict[str, str]:
    """Update a project's name or visibility. Requires project access.

    Only fields provided in the query string are modified.
    """
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project is None:
        return {"error": "Project not found"}

    if is_public is not None:
        project.is_public = is_public

    if name is not None:
        project.name = name

    session.add(project)
    session.commit()
    session.refresh(project)
    return {"status": "OK"}


@router.delete("/{project_id}", dependencies=[Depends(get_current_user_with_project_access)])
async def delete_project(project_id: str, session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    """Delete a project and all its user-access links. Requires project access."""
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project is None:
        return {"error": "Project not found"}

    user_links = session.exec(select(ProjectUserLink).where(ProjectUserLink.project_id == project.id)).all()
    for link in user_links:
        session.delete(link)

    session.delete(project)
    session.commit()
    return {"status": "OK"}


@router.post(
    "/{project_id}/access/{user_id}",
    dependencies=[Depends(get_current_user_with_project_access)],
)
async def add_user_to_project(
    project_id: str, user_id: str, session: Annotated[Session, Depends(get_session)]
) -> dict[str, str]:
    """Grant a user access to a project by creating a ``ProjectUserLink``. Requires project access."""
    link = ProjectUserLink(project_id=project_id, user_id=user_id)
    session.add(link)
    session.commit()
    return {"status": "OK"}


@router.delete(
    "/{project_id}/access/{user_id}",
    dependencies=[Depends(get_current_user_with_project_access)],
)
async def remove_user_from_project(
    project_id: str, user_id: str, session: Annotated[Session, Depends(get_session)]
) -> dict[str, str]:
    """Revoke a user's access to a project by deleting the ``ProjectUserLink``. Requires project access."""
    statement = select(ProjectUserLink).where(
        ProjectUserLink.project_id == project_id, ProjectUserLink.user_id == user_id
    )
    link = session.exec(statement).first()

    if link is None:
        return {"error": "Link not found"}

    session.delete(link)
    session.commit()
    return {"status": "OK"}
