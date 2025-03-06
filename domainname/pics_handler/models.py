from django.db import models
from django.urls import reverse

class BaseModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата и время обновления')

    class Meta:
        abstract = True                                         # Указываем, что это абстрактная модель

class Docs(BaseModel):

    file_path = models.FileField(upload_to='media/', verbose_name='Путь к файлу') # строка, которая содержит путь к файлу
    file_original_name = models.CharField(max_length=255, default='image.jpg', verbose_name='Имя файла') # Имя файла для вывода на главную, например
    size = models.IntegerField(verbose_name='Размер файла')                                               # размер файла в Кб

    class Meta:
        verbose_name = 'Загруженные картинки'
        verbose_name_plural = 'Загруженные картинки'
        db_table = 'docs'

class UsersToDocs(BaseModel):

    username = models.CharField(max_length=255, verbose_name='Логин пользователя') # имя пользователя
    docs_id = models.ForeignKey(Docs, on_delete=models.CASCADE, verbose_name='ID картинки из таблицы Загруженные картинки')
    # FK на таблицу docs при загрузке нового файла, будет делаться такая запись

    class Meta:
        verbose_name = 'Пользователи картинок'
        verbose_name_plural = 'Пользователи картинок'
        db_table = 'users_to_docs'