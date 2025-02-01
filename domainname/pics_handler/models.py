from django.db import models

class BaseModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True                                         # Указываем, что это абстрактная модель

class Docs(BaseModel):

    file_path = models.FileField(upload_to='media/')            # строка, которая содержит путь к файлу
    file_original_name = models.CharField(max_length=255, default='image.jpg')       # Имя файла для вывода на главную, например
    size = models.IntegerField()                                # размер файла в Кб

class UsersToDocs(BaseModel):

    username = models.CharField(max_length=255)                 # имя пользователя
    docs_id = models.ForeignKey(Docs, on_delete=models.CASCADE) # FK на таблицу docs при загрузке нового файла,
                                                                # будет делаться такая запись