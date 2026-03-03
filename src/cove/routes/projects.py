from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from cove.models.projects import Project, ProjectUserLink

from ..dependencies import get_session
from ..models.users import User
from ..services.auth import (
    does_user_have_access_to_project,
    get_current_user,
    get_current_user_non_fatal,
    get_current_user_with_project_access,
)

router = APIRouter(prefix="/project")


@router.get("/")
async def get_all_projects(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User | None, Depends(get_current_user_non_fatal)],
) -> Sequence[Project]:
    statement = select(Project)
    results = session.exec(statement)

    projects = results.all()

    public_projects = [project for project in projects if project.is_public]

    private_projects_with_access = []

    if current_user is not None:
        private_projects_with_access = [
            project
            for project in projects
            if not project.is_public and await does_user_have_access_to_project(session, current_user, project.id)
        ]

    return public_projects + private_projects_with_access


@router.post("/{name}")
async def create_project(
    name: str,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
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
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project:
        if is_public is not None:
            project.is_public = is_public

        if name is not None:
            project.name = name

        session.add(project)
        session.commit()
        session.refresh(project)
        return {"status": "OK"}
    else:
        return {"error": "Project not found"}


@router.delete("/{project_id}", dependencies=[Depends(get_current_user_with_project_access)])
async def delete_project(project_id: str, session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project:
        user_links = session.exec(select(ProjectUserLink).where(ProjectUserLink.project_id == project.id)).all()
        for link in user_links:
            session.delete(link)

        session.delete(project)
        session.commit()
        return {"status": "OK"}
    else:
        return {"error": "Project not found"}
