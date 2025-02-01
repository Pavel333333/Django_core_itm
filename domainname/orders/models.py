from django.contrib.auth.models import User
from django.db import models

from pics_handler.models import BaseModel, Docs, UsersToDocs


class Price(BaseModel):

    EXTENSIONS = [
        ("jpg", "JPEG Image"),
        ("pdf", "PDF Document"),
        ("png", "PNG Image"),
    ]

    file_type = models.CharField(choices=EXTENSIONS, unique=True) # расширение файлов, которые наш сервис
                                                                  # умеет распознавать (анализировать)
    price = models.FloatField()                                   # float, цена анализ 1 Кб данных, будем в будущем
                                                                  # считать цену за анализ файла


class Cart(BaseModel):

    user_id = models.ForeignKey(User, on_delete=models.CASCADE) # FK на встроенную в Django таблицу user-ов,
                                                                       # если писали свою систему аутентификации,
                                                                       # то тогда на вашу таблицу пользователей.
                                                                       # на id пользователя
    docs_id = models.ForeignKey(Docs, on_delete=models.CASCADE)        # FK на таблицу docs
    order_price = models.FloatField()                                  # float цена заказа, высчитывается при добавлении
                                                                       # файла на основании его типа, размера и цены в таблице price
    payment = models.BooleanField()                                    # булева отметка об оплате cервиса оплаты у нас
                                                                       # не будет, но номинально мы просто будем менять
                                                                       # статус с по умолчанию при создании заказа
                                                                       # с False на True

