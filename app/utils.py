from app.core.email import EmailSender
from app.core.config import settings
from app.api.deps import SessionDep, CurrentUser
from app.models import Group, GroupRequest, UserGroupLink
from fastapi import HTTPException, status



def send_general_mail(email: str, name: str, subject: str = "Welcome to Our Service"):
    try:
        # Verify API credentials exist
        api_key = settings.MAILJET_API_KEY
        api_secret = settings.MAILJET_SECRET_KEY
        
        if not api_key or not api_secret:
            return {
                "success": False,
                "error": "Missing Mailjet API credentials in settings"
            }
        
        print(f"Using API Key: {api_key[:4]}...{api_key[-4:] if len(api_key) > 8 else ''}")
        
        email_sender = EmailSender(api_key=api_key, api_secret=api_secret)
        result = email_sender.send_general_email(
            email=email,
            name=name,
            subject=subject
        )
        return result
    except Exception as e:
        error_details = str(e)
        print(f"Exception in send_general_mail: {error_details}")
        return {
            "success": False,
            "error": error_details
        }
        
def check_group_permission(
    session: SessionDep,
    group_id: GroupRequest,
    current_user: CurrentUser,
    required_role: str = "admin"   
) -> bool:
    if current_user.is_superuser:
        return True
    
    user_link = session.exec(
        select(UserGroupLink).where(
            UserGroupLink.user_id == current_user.id,
            UserGroupLink.group_id == group_id
        )
    ).first()
    
    if not user_link:
        return False
    
    if required_role == "admin" and user_link.role == "admin":
        return True
    return False

def require_permission(
    session: SessionDep,
    group_id: GroupRequest,
    current_user: CurrentUser,
    required_role: str = "admin"
):
    has_permission = check_group_permission(
        session=session,
        group_id=group_id,  
        current_user=current_user,
        required_role=required_role
    )
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required permissions"
        )