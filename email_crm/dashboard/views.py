from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from contacts.models import Contact
from emails.models import SentEmail, EmailTemplate
from .models import Activity
from .serializers import ActivitySerializer
from django.db.models import Count, Avg, Q
from django.utils import timezone
import datetime
from django.contrib.auth.decorators import login_required
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class DashboardView(APIView):
    """
    API view to get dashboard summary information.
    
    GET: Retrieve a summary of user's CRM activities
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard summary information."""
        try:
            user = request.user
            logger.info(f"Dashboard data requested by user: {user.username}")
            
            # Get contact count
            contact_count = Contact.objects.filter(user=user).count()
            
            # Email stats
            total_emails_sent = SentEmail.objects.filter(user=user).count()
            today = timezone.now().date()
            emails_today = SentEmail.objects.filter(
                user=user,
                sent_at__date=today
            ).count()
            
            # Open and click rates
            opened_emails = SentEmail.objects.filter(user=user, opened=True).count()
            clicked_emails = SentEmail.objects.filter(user=user, clicked=True).count()
            
            # Calculate rates
            open_rate = (opened_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
            click_rate = (clicked_emails / total_emails_sent * 100) if total_emails_sent > 0 else 0
            
            # Recent activities
            recent_activities = Activity.objects.filter(user=user).order_by('-timestamp')[:10]
            
            # Recent emails
            recent_emails = SentEmail.objects.filter(user=user).order_by('-sent_at')[:5]
            recent_email_data = [
                {
                    'id': email.id,
                    'contact_name': email.contact.name,
                    'subject': email.subject,
                    'sent_at': email.sent_at,
                    'opened': email.opened,
                    'clicked': email.clicked
                }
                for email in recent_emails
            ]
            
            logger.info(f"Dashboard data successfully retrieved for user: {user.username}")
            
            return Response({
                'contact_count': contact_count,
                'total_emails_sent': total_emails_sent,
                'emails_today': emails_today,
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'recent_activities': ActivitySerializer(recent_activities, many=True).data,
                'recent_emails': recent_email_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving dashboard data: {str(e)}")
            return Response({
                'error': 'An error occurred while retrieving dashboard data',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StatsView(APIView):
    """
    API view to get detailed statistics for the dashboard.
    
    GET: Retrieve detailed statistics on contacts, emails, and activities
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get detailed statistics for the dashboard."""
        user = request.user
        
        # Emails per day (last 7 days)
        today = timezone.now().date()
        seven_days_ago = today - datetime.timedelta(days=7)
        
        emails_per_day = []
        for i in range(7):
            day = seven_days_ago + datetime.timedelta(days=i)
            count = SentEmail.objects.filter(
                user=user,
                sent_at__date=day
            ).count()
            emails_per_day.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': count
            })
        
        # Top contacts by email count
        top_contacts = SentEmail.objects.filter(user=user) \
            .values('contact__name', 'contact__email') \
            .annotate(email_count=Count('id')) \
            .order_by('-email_count')[:5]
        
        # Open and click rates for each template
        template_stats = SentEmail.objects.filter(user=user, template__isnull=False) \
            .values('template__name') \
            .annotate(
                sent_count=Count('id'),
                opened_count=Count('id', filter=Q(opened=True)),
                clicked_count=Count('id', filter=Q(clicked=True))
            )
        
        # Format template stats
        formatted_template_stats = []
        for stat in template_stats:
            sent = stat['sent_count']
            open_rate = round((stat['opened_count'] / sent * 100), 2) if sent > 0 else 0
            click_rate = round((stat['clicked_count'] / sent * 100), 2) if sent > 0 else 0
            
            formatted_template_stats.append({
                'template_name': stat['template__name'],
                'sent_count': sent,
                'opened_count': stat['opened_count'],
                'clicked_count': stat['clicked_count'],
                'open_rate': open_rate,
                'click_rate': click_rate
            })
        
        # Contacts by company
        company_distribution = Contact.objects.filter(user=user) \
            .values('company') \
            .annotate(count=Count('id')) \
            .order_by('-count')
        
        return Response({
            'emails_per_day': emails_per_day,
            'top_contacts': top_contacts,
            'template_stats': formatted_template_stats,
            'company_distribution': company_distribution
        }, status=status.HTTP_200_OK)

class RecentActivitiesView(APIView):
    """
    API view to get recent user activities.
    
    GET: Retrieve recent activities for the user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get recent activities for the user."""
        user = request.user
        limit = int(request.query_params.get('limit', 20))
        
        # Get activities
        activities = Activity.objects.filter(user=user).order_by('-timestamp')[:limit]
        
        return Response({
            'activities': ActivitySerializer(activities, many=True).data
        }, status=status.HTTP_200_OK)

# Template Views
@login_required
def dashboard_view(request):
    """Render the dashboard page template."""
    return render(request, 'dashboard/dashboard.html')
