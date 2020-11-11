import uuid
from datetime import timedelta
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.postgres.fields import JSONField
from djmoney.models.fields import MoneyField
from launchlab_django_utils.models import UUIDTimestampedModel
from concurrency.fields import IntegerVersionField
from simple_history.models import HistoricalRecords


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = IntegerVersionField()
    email = models.fields.EmailField()
    nickname = models.fields.CharField(max_length=32, unique=True)
    blocked = models.fields.BooleanField(default=False)
    note = models.fields.TextField()
    USERNAME_FIELD = 'nickname'
    objects = UserManager()

    @property
    def is_active(self):
        return not self.blocked

    @property
    def is_staff(self):
        return self.is_active


class BillManager(models.Manager):
    def paid(self):
        return self.get_queryset().filter(paid_at__isnull=False)

    def unpaid(self):
        return self.get_queryset().filter(paid_at__isnull=True)

    def paid_by_cash(self):
        return self.paid().filter(metadata__type='cash')

    def paid_online(self):
        return self.paid().filter(metadata__type='card')

    def must_be_paid_today(self):
        today = now().date()
        return self.unpaid().filter(due__gte=today, due__lt=today+timedelta(days=1))


class Bill(UUIDTimestampedModel):
    amount = MoneyField(max_digits=8, decimal_places=4, default_currency='USD')
    due = models.fields.DateTimeField()
    version = IntegerVersionField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paid_at = models.fields.DateTimeField(default=None, blank=True, null=True)
    metadata = JSONField()
    history = HistoricalRecords()
    objects = BillManager()

    @property
    def payment_type(self):
        return self.metadata.get('type')