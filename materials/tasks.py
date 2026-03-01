from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def notify_course_subscribers(course_id):
    """
    Задача для уведомления подписчиков курса о его обновлении
    """
    from materials.models import Course, Subscription

    try:
        course = Course.objects.select_related('owner').get(id=course_id)
        subscribers = Subscription.objects.filter(
            course=course,
            is_active=True
        ).select_related('user')

        if not subscribers.exists():
            logger.info(f"Нет подписчиков для курса {course.title}")
            return f"Нет подписчиков для курса {course.title}"

        success_count = 0
        fail_count = 0

        for subscription in subscribers:
            user = subscription.user
            if user.email:
                try:
                    # Контекст для шаблона
                    context = {
                        'username': user.username or user.email.split('@')[0],
                        'course_title': course.title,
                        'course_url': f"{settings.BASE_URL}/courses/{course.id}/",
                        'year': timezone.now().year
                    }

                    # Рендерим HTML-шаблон
                    html_message = render_to_string(
                        'materials/emails/course_update_message.html',
                        context
                    )

                    # Рендерим текстовую версию (для почтовых клиентов без HTML)
                    plain_message = strip_tags(html_message)

                    # Рендерим тему
                    subject = render_to_string(
                        'materials/emails/course_update_subject.html',
                        context
                    ).strip()  # .strip() убирает лишние пробелы и переносы строк

                    # Отправляем email
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    success_count += 1
                    logger.info(f"Email отправлен пользователю {user.email}")

                except Exception as e:
                    fail_count += 1
                    logger.error(f"Ошибка отправки email пользователю {user.email}: {str(e)}")

        return {
            'status': 'success',
            'course_id': course_id,
            'course_title': course.title,
            'total_subscribers': subscribers.count(),
            'emails_sent': success_count,
            'emails_failed': fail_count
        }

    except Course.DoesNotExist:
        error_msg = f"Курс с id {course_id} не найден"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"Неожиданная ошибка: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg
        }