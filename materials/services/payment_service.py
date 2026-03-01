from config import settings
from materials.models import Payment
from materials.services.stripe_service import StripeService


class PaymentService:
    """
    Сервис для управления платежами в приложении
    """

    @staticmethod
    def create_payment(user, course, amount, payment_method='card'):
        """
        Создание платежа и интеграция со Stripe
        """
        # 1. Создаем платеж в нашей БД (в статусе pending)
        payment = Payment.objects.create(
            user=user,
            course=course,
            amount=amount,
            payment_method=payment_method,
            status=Payment.PaymentStatus.PENDING
        )

        # 2. Создаем продукт в Stripe
        product_result = StripeService.create_product(
            name=course.title,
            description=course.description[:200] if course.description else ""
        )

        if not product_result['success']:
            payment.status = Payment.PaymentStatus.FAILED
            payment.save()
            return {
                'success': False,
                'error': f"Ошибка создания продукта: {product_result['error']}"
            }

        payment.stripe_product_id = product_result['product_id']
        payment.save()

        # 3. Создаем цену в Stripe
        price_result = StripeService.create_price(
            amount=amount,
            product_id=product_result['product_id']
        )

        if not price_result['success']:
            payment.status = Payment.PaymentStatus.FAILED
            payment.save()
            return {
                'success': False,
                'error': f"Ошибка создания цены: {price_result['error']}"
            }

        payment.stripe_price_id = price_result['price_id']
        payment.save()

        # 4. Создаем сессию для оплаты
        success_url = f"{settings.BASE_URL}/api/payments/success/?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.BASE_URL}/api/payments/cancel/"

        session_result = StripeService.create_checkout_session(
            price_id=price_result['price_id'],
            success_url=success_url,
            cancel_url=cancel_url
        )

        if not session_result['success']:
            payment.status = Payment.PaymentStatus.FAILED
            payment.save()
            return {
                'success': False,
                'error': f"Ошибка создания сессии: {session_result['error']}"
            }

        # 5. Обновляем платеж данными из Stripe
        payment.stripe_session_id = session_result['session_id']
        payment.payment_url = session_result['session_url']
        payment.save()

        return {
            'success': True,
            'payment': payment,
            'payment_url': session_result['session_url'],
            'session_id': session_result['session_id']
        }

    @staticmethod
    def check_payment_status(payment_id):
        """
        Проверка статуса платежа через Stripe
        """
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return {
                'success': False,
                'error': 'Платеж не найден'
            }

        if not payment.stripe_session_id:
            return {
                'success': False,
                'error': 'Платеж не связан с сессией Stripe'
            }

        # Получаем информацию о сессии из Stripe
        session_result = StripeService.retrieve_session(payment.stripe_session_id)

        if not session_result['success']:
            return {
                'success': False,
                'error': session_result['error']
            }

        # Обновляем статус платежа в БД
        payment_status = session_result['payment_status']

        if payment_status == 'paid':
            payment.status = Payment.PaymentStatus.PAID
            if session_result.get('payment_intent'):
                payment.stripe_payment_intent_id = session_result['payment_intent']
        elif payment_status == 'unpaid':
            payment.status = Payment.PaymentStatus.PENDING
        else:
            payment.status = Payment.PaymentStatus.FAILED

        payment.save()

        return {
            'success': True,
            'payment': payment,
            'stripe_status': payment_status,
            'payment_status': payment.status
        }