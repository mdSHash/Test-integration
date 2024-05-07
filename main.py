from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
   choice_text: str
   is_correct: bool


class QuestionBase(BaseModel):
   question_text: str
   choice: List[ChoiceBase]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/questions/{question_id}")
async def read_question(question_id: int, db: db_dependency):
    result = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Question not found")
    return result

@app.get("/choices/{question_id}")
async def read_choices(question_id: int, db: db_dependency):
    result = db.query(models.Choice).filter(models.Choice.question_id == question_id).all()
    if not result:
        raise HTTPException(status_code=404, detail="Choices not found")
    return result

@app.post("/questions/")
async def create_question(question: QuestionBase, db: db_dependency):
    question_obj = models.Question(question_text=question.question_text)
    db.add(question_obj)
    db.commit()
    db.refresh(question_obj)
    for choice in question.choice:
        choice_obj = models.Choice(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=question_obj.id)
        db.add(choice_obj)   
    db.commit()