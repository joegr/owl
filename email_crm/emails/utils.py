import re
from django.utils import timezone

class EmailTemplateProcessor:
    """
    Utility class for processing email templates and replacing variables.
    """
    
    @staticmethod
    def process_template(template_text, contact):
        """
        Replace template variables with values from the contact.
        
        Args:
            template_text: The template text containing variables
            contact: The Contact object with the replacement values
            
        Returns:
            The processed text with variables replaced
        """
        if not template_text:
            return ""
            
        # Basic replacements
        replacements = {
            '{{name}}': contact.name,
            '{{email}}': contact.email,
            '{{company}}': contact.company or '',
            '{{position}}': contact.position or '',
            '{{phone}}': contact.phone or '',
            '{{date}}': timezone.now().strftime('%B %d, %Y'),
            '{{day}}': timezone.now().strftime('%A'),
            '{{time}}': timezone.now().strftime('%H:%M'),
        }
        
        # Add any custom fields from the contact model dynamically
        # This assumes any additional fields might be added in the future
        for field in contact._meta.get_fields():
            field_name = field.name
            if field_name not in ['id', 'user', 'created_at', 'updated_at', 'received_emails']:
                try:
                    value = getattr(contact, field_name)
                    if value is not None:
                        replacements[f'{{{{contact.{field_name}}}}}'] = str(value)
                except (AttributeError, ValueError):
                    pass
        
        # Process each replacement
        result = template_text
        for var, value in replacements.items():
            result = result.replace(var, value)
            
        return result
        
    @staticmethod
    def generate_html_version(text):
        """
        Convert plain text email to a basic HTML version.
        
        Args:
            text: The plain text email content
            
        Returns:
            HTML version of the email with basic formatting
        """
        if not text:
            return "<html><body></body></html>"
            
        # Replace newlines with <br> tags
        html = text.replace('\n', '<br>\n')
        
        # Wrap in HTML structure
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.5; }}
                p {{ margin-bottom: 1em; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        return html 