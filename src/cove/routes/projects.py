from typing import Annotated, Sequence
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..dependencies import get_session
from cove.models.projects import Project


router = APIRouter(prefix="/project")


@router.get("/")
async def get_all_projects(session: Annotated[Session, Depends(get_session)]) -> Sequence[Project]:
    statement = select(Project)
    results = session.exec(statement)

    return results.all()


@router.post("/{name}")
async def create_project(name: str, session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    project = Project(name=name, is_public=False)

    session.add(project)
    session.commit()
    session.refresh(project)
    return {"status": "OK", "project_id": project.id}


@router.patch("/{project_id}")
async def toggle_project_visibility(
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


@router.delete("/{project_id}")
async def delete_project(project_id: str, session: Annotated[Session, Depends(get_session)]) -> dict[str, str]:
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project:
        session.delete(project)
        session.commit()
        return {"status": "OK"}
    else:
        return {"error": "Project not found"}
