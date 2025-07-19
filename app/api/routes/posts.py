# This was for testing purposes 

from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List, Any
from pydantic import BaseModel, EmailStr
from app.models import (
    Post, 
    BasePost, 
    PostResponse, 
    Message, 
    Room
)
from app.api.deps import CurrentUser, get_current_user, SessionDep
from app.crud import create_post
from datetime import datetime, timezone

router = APIRouter()


def post_error(post):
    if not post:
        raise HTTPException(status_code=404, detail="Post Not Found")


def check_post_owner(post: Post, user_id: str):
    if str(post.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this post",
        )


@router.post("/create-post", response_model=PostResponse)
async def post_regsiter(
    user_in: BasePost,
    session: SessionDep,  
    current_user: CurrentUser 
) -> Any:
    post_data = BasePost.model_validate(user_in) 
    
    new_post = await create_post(
        session=session,
        post_register=post_data, 
        current_user=current_user
    )
    
    return PostResponse(
        id=str(new_post.id), 
        title=new_post.title,
        content=new_post.content,
        tags=new_post.tags,
        user_id=new_post.user_id,
        user_email=new_post.user_email,
        published=new_post.published,
        created_at=new_post.created_at,
        updated_at=new_post.updated_at
    )

    
@router.get("/get-all-posts", response_model=List[PostResponse])
async def get_posts(current_user: CurrentUser):
    posts = await Post.find_all().to_list()
    return posts


@router.get("/my-posts", response_model=List[PostResponse])
async def get_my_posts(current_user: CurrentUser):
    posts = await Post.find(Post.user_id == current_user.id).to_list()
    return posts


@router.get("/get-post/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, current_user: CurrentUser):
    post = await Post.get(post_id)
    post_error(post)
    return post


@router.put("/update-post/{post_id}", response_model=PostResponse)
async def update_post(post_id: str, request: BasePost, current_user: CurrentUser):
    post = await Post.get(post_id)
    post_error(post)
    check_post_owner(post, current_user.id)

    update_data = request.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc)

    await post.update({"$set": update_data})
    return await Post.get(post_id)


@router.delete("/delete/{post_id}", response_model=Message)
async def delete_post(post_id: str, current_user: CurrentUser):
    post = await Post.get(post_id)
    post_error(post)
    check_post_owner(post, current_user.id)

    await post.delete()
    return Message(message="Post deleted successfully")


@router.post('/test-room')
async def test_create_room():
    room = Room(participants=["user_a", "user_b"])
    await room.insert()
    return {
        "room_id": str(room.id)
    }
