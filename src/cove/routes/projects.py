from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..dependencies import get_session
from cove.models.projects import Project


router = APIRouter(prefix="/project")


@router.get("/")
async def get_all_projects(session: Annotated[Session, Depends(get_session)]):
    statement = select(Project)
    results = session.exec(statement)

    return results.all()


@router.post("/{name}")
async def create_project(name: str, session: Annotated[Session, Depends(get_session)]):
    project = Project(name=name, is_public=False)

    session.add(project)
    session.commit()
    session.refresh(project)
    return {"status": "OK", "project_id": project.id}


@router.patch("/{project_id}/public")
async def toggle_project_visibility(
    project_id: str, is_public: bool, session: Annotated[Session, Depends(get_session)]
):
    statement = select(Project).where(Project.id == project_id)
    project = session.exec(statement).first()

    if project:
        project.is_public = is_public
        session.add(project)
        session.commit()
        session.refresh(project)
        return {"status": "OK"}
    else:
        return {"error": "Project not found"}
