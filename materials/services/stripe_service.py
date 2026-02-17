import stripe
from django.conf import settings

# Инициализация Stripe с секретным ключом
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """
    Сервис для работы с API Stripe
    """

    @staticmethod
    def create_product(name, description=""):
        """
        Создание продукта в Stripe
        """
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
            )
            return {
                'success': True,
                'product_id': product.id,
                'product_data': product
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def create_price(amount, product_id, currency="rub"):
        """
        Создание цены для продукта в Stripe
        """
        try:
            # Конвертируем рубли в копейки
            amount_in_kopecks = int(amount * 100)

            price = stripe.Price.create(
                unit_amount=amount_in_kopecks,
                currency=currency,
                product=product_id,
            )
            return {
                'success': True,
                'price_id': price.id,
                'price_data': price
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url):
        """
        Создание сессии для оплаты
        """
        try:
            session = stripe.checkout.Session.create(
                success_url=success_url,
                cancel_url=cancel_url,
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
            )
            return {
                'success': True,
                'session_id': session.id,
                'session_url': session.url,
                'session_data': session
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def retrieve_session(session_id):
        """
        Получение информации о сессии оплаты
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'success': True,
                'session_data': session,
                'payment_status': session.payment_status,
                'payment_intent': session.payment_intent
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

