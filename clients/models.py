from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='Клиент',
        related_name='clients'
    )
    tg_user_id = models.BigIntegerField(
        'Телеграм ID',
        unique=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f'{self.tg_user_id} {self.email}'
