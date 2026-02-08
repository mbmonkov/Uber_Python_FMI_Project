"""
This module manages the communication system within the platform.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import get_db

router = APIRouter(tags=["Messages"])


@router.post("/messages/send")
def send_message(sender_id: int, receiver_id: int, content: str, db: Session = Depends(get_db)):
    """ Records a new message in the database between two users. """
    if not content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty.")

    new_msg = models.Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )

    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    return {
        "message": "Message sent successfully",
        "message_id": new_msg.id
    }


@router.get("/messages/{user_id}")
def get_my_messages(user_id: int, db: Session = Depends(get_db)):
    """ Retrieves all received messages for a specific user, including the sender's name. """
    user_exists = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found.")

    messages = db.query(models.Message).filter(models.Message.receiver_id == user_id
                                               ).order_by(models.Message.id.desc()).all()

    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "sender_id": msg.sender_id,
            "sender_name": msg.sender.full_name
        })

    return {
        "count": len(result),
        "messages": result
    }


@router.get("/messages/chat/{user_one_id}/{user_two_id}")
def get_chat_history(user_one_id: int, user_two_id: int, db: Session = Depends(get_db)):
    """ Retrieves the full chat history between two users, including sender names and ownership flags. """
    cond_1 = (models.Message.sender_id == user_one_id) & (models.Message.receiver_id == user_two_id)
    cond_2 = (models.Message.sender_id == user_two_id) & (models.Message.receiver_id == user_one_id)

    messages = db.query(models.Message).filter(cond_1 | cond_2).order_by(models.Message.id.asc()).all()

    history = []
    for msg in messages:
        history.append({
            "sender_name": msg.sender.full_name,
            "content": msg.content,
            "is_me": msg.sender_id == user_one_id
        })

    return {
        "chat_history": history
    }
