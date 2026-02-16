import re
from rest_framework.serializers import ValidationError

def validate_youtube_url(value):
    """
    Проверяет, что ссылка ведет на youtube.com
    Если ссылка не является youtube-ссылкой или ссылка отсутствует, пропускаем.
    """
    if not value:
        return value

    # Проверяем, что это YouTube
    youtube_pattern = [
        r'^https?://(www\.)?youtube\.com',
        r'^https?://(www\.)?youtu\.be',
        r'^https?://(www\.)?m\.youtube\.com'
    ]
    for pattern in youtube_pattern:
        if re.match(pattern, value):
            return value

    # Если ни один паттерн не подошел
    raise ValidationError(
        'Разрешены только ссылки на YouTube (youtube.com или youtu.be). '
        'Ссылки на сторонние ресурсы запрещены.'
    )

