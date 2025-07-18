# import os
# from pathlib import Path
# import datetime
# from jinja2 import Template
# from app.core.config import settings
# from typing import Dict, Any
# from mailjet_rest import Client

# class EmailSender:
#     def __init__(self, api_key: str, api_secret: str):
#         """Initialize the email sender with Mailjet credentials"""
#         self.mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        
#     def send_email(
#         self,
#         subject: str,
#         html_content: str,
#         text_content: str,
#         from_email: str = "jester.mest@gmail.com",
#         from_name: str = "Emily",
#         recipient_email: str = "jeffreymintah737@gmail.com",
#         recipient_name: str = "Jeffrey Mintah",
#     ) -> dict:
#         """Send an email using Mailjet API with improved error handling"""
#         # Validate inputs
#         if not recipient_email or not recipient_name:
#             raise ValueError("Recipient email and name must be provided")
            
#         # Prepare the Mailjet data structure
#         data = {
#             'Messages': [
#                 {
#                     "From": {
#                         "Email": from_email,
#                         "Name": from_name
#                     },
#                     "To": [
#                         {
#                             "Email": recipient_email,
#                             "Name": recipient_name
#                         }
#                     ],
#                     "Subject": subject,
#                     "TextPart": text_content,
#                     "HTMLPart": html_content
#                 }
#             ]
#         }
        
#         # Send the email
#         try:
#             print(f"Attempting to send email to {recipient_email} with subject: {subject}")
#             result = self.mailjet.send.create(data=data)
#             response_data = result.json()
#             print(f"Mailjet API response: {response_data}")
            
#             return {
#                 "success": result.status_code == 200,
#                 "status_code": result.status_code,
#                 "response": response_data
#             }
#         except Exception as e:
#             error_details = str(e)
#             print(f"Failed to send email: Detailed error: {error_details}")
#             return {
#                 "success": False,
#                 "error": error_details
#             }

#     def render_html_template(self, context: Dict[str, Any]) -> str:
#         """Render a simple HTML template with the given context"""
#         try:
#             # Simple HTML template as a string
#             html_content = """
#             <!DOCTYPE html>
#             <html>
#             <head>
#                 <meta charset="UTF-8">
#                 <title>Welcome Email</title>
#                 <style>
#                     body {
#                         font-family: Arial, sans-serif;
#                         line-height: 1.6;
#                         color: #333;
#                         margin: 0;
#                         padding: 20px;
#                     }
#                     .container {
#                         max-width: 600px;
#                         margin: 0 auto;
#                         padding: 20px;
#                         background-color: #f9f9f9;
#                     }
#                     .button {
#                         display: inline-block;
#                         padding: 10px 20px;
#                         background-color: #007bff;
#                         color: #ffffff;
#                         text-decoration: none;
#                         border-radius: 4px;
#                     }
#                 </style>
#             </head>
#             <body>
#                 <div class="container">
#                     <h3>Hello {{ recipient_name }}!</h3>
#                     <p>Welcome to our service! We're excited to have you on board.</p>
#                     <p><a href="{{ action_url }}" class="button">Visit Your Account</a></p>
#                     <p>Best regards,<br>The Team</p>
#                     <p>© {{ current_year }} Your Company</p>
#                 </div>
#             </body>
#             </html>
#             """
            
#             # Add current year to context
#             context['current_year'] = datetime.datetime.now().year
            
#             # Render the HTML template with Jinja2
#             template = Template(html_content)
#             rendered_html = template.render(**context)
            
#             return rendered_html
#         except Exception as e:
#             error_msg = f"Error rendering HTML template: {str(e)}"
#             print(error_msg)
#             raise Exception(error_msg)
    
#     def send_general_email(self, email: str, name: str, subject: str = "Welcome Message") -> dict:
#         """Send a general email using a simple HTML template"""
#         try:
#             # Context for the template
#             context = {
#                 "recipient_name": name,
#                 "action_url": "https://yourwebsite.com/account",
#                 "current_year": datetime.datetime.now().year
#             }
            
#             # Render the template
#             html_content = self.render_html_template(context)
            
#             # Plain text version
#             text_content = f"Hello {name},\n\nThank you for using our service. We're excited to have you on board!\n\nVisit your account: https://yourwebsite.com/account\n\nBest regards,\nThe Team"
            
#             # Send the email
#             return self.send_email(
#                 recipient_email=email,
#                 recipient_name=name,
#                 subject=subject,
#                 html_content=html_content,
#                 text_content=text_content
#             )
#         except Exception as e:
#             error_details = str(e)
#             print(f"Failed to send general email: {error_details}")
#             return {
#                 "success": False,
#                 "error": error_details
#             }