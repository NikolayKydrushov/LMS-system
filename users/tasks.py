from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging
from users.models import User

logger = logging.getLogger(__name__)


@shared_task
def block_inactive_users():
    """
    Задача для блокировки пользователей, которые не заходили более месяца
    Запускается по расписанию через celery-beat
    """
    try:
        # Вычисляем дату месяц назад
        month_ago = timezone.now() - timedelta(days=30)

        # Находим пользователей, которые: не заходили более месяца, активны, не суперпользователи
        inactive_users = User.objects.filter(
            is_active=True,
            is_superuser=False  # Не блокируем суперпользователей
        ).filter(
            # Пользователи, которые либо никогда не заходили, либо заходили более месяца назад
            last_login__lt=month_ago
        )

        # Считаем количество найденных пользователей
        count = inactive_users.count()

        if count == 0:
            logger.info("Нет неактивных пользователей для блокировки")
            return {
                'status': 'success',
                'message': 'Нет пользователей для блокировки',
                'blocked_count': 0,
                'date': timezone.now().date().isoformat()
            }

        # Сохраняем информацию о блокируемых пользователях для лога
        blocked_users_info = []
        for user in inactive_users:
            last_login_str = user.last_login.isoformat() if user.last_login else 'никогда'
            blocked_users_info.append({
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'last_login': last_login_str
            })

        # Блокируем найденных пользователей
        inactive_users.update(is_active=False)

        # Отправляем уведомления заблокированным пользователям (опционально)
        send_block_notifications.delay(blocked_users_info)

        logger.info(f"Заблокировано {count} неактивных пользователей")

        return {
            'status': 'success',
            'message': f'Заблокировано {count} неактивных пользователей',
            'blocked_count': count,
            'blocked_users': blocked_users_info,
            'date': timezone.now().date().isoformat()
        }

    except Exception as e:
        error_msg = f"Ошибка при блокировке неактивных пользователей: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'error': error_msg,
            'date': timezone.now().date().isoformat()
        }


@shared_task
def send_block_notifications(blocked_users_info):
    """
    Отправляет уведомления пользователям о блокировке (опционально)
    """
    try:

        # Отправляем отчет админу
        if blocked_users_info and settings.ADMIN_EMAIL:
            context = {
                'blocked_users': blocked_users_info,
                'total': len(blocked_users_info),
                'date': timezone.now().date().isoformat()
            }

            html_message = render_to_string(
                'users/inactive_users_report.html',
                context
            )

            send_mail(
                subject=f'Отчет о блокировке неактивных пользователей за {timezone.now().date()}',
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message,
                fail_silently=True,
            )

        return f"Уведомления отправлены для {len(blocked_users_info)} пользователей"

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений о блокировке: {str(e)}")
        return f"Ошибка отправки уведомлений: {str(e)}"


@shared_task
def send_course_update_email(user_email, course_title):
    """
    Задача для отправки email об обновлении курса
    """
    try:
        # Контекст для шаблона
        context = {
            'course_title': course_title,
            'year': timezone.now().year
        }

        # Рендерим HTML-шаблон
        html_message = render_to_string(
            'users/course_update_message.html',
            context
        )

        # Отправляем email
        send_mail(
            subject=f'Курс "{course_title}" обновлен',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Email отправлен на {user_email}")
        return f"Email отправлен на {user_email}"

    except Exception as e:
        logger.error(f"Ошибка отправки email на {user_email}: {str(e)}")
        return f"Ошибка отправки email: {str(e)}"