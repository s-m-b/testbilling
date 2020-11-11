from django import forms
from django.forms.fields import ValidationError
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from djmoney.forms.fields import MoneyField, Money
from simple_history.admin import SimpleHistoryAdmin
from .models import User, Bill


class BillChangeAdminForm(forms.ModelForm):
    meta_type = forms.ChoiceField(required=True, choices=(('cash', 'Cash'), ('card', 'Card')))
    meta_code = forms.CharField(required=False)
    meta_url = forms.URLField(required=False)
    meta_amount = MoneyField(required=False, max_digits=8, decimal_places=4, default_currency='USD')

    class Meta:
        model = Bill
        exclude = ('metadata',)

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        initial = kwargs.pop('initial', {})
        if instance is not None and instance.metadata is not None:
            meta = instance.metadata
            initial['meta_type'] = meta.get('type')
            initial['meta_code'] = meta.get('code')
            initial['meta_url'] = meta.get('url')
            amount = meta.get('amount')
            if amount is not None:
                initial['meta_amount'] = Money(amount=amount, currency='USD')
        super().__init__(*args, instance=instance, initial=initial, **kwargs)

    def clean(self):
        data = super().clean()
        _type = data.get('meta_type')
        code = data.get('meta_code')
        url = data.get('meta_url')
        amount = data.get('meta_amount')
        if _type == 'cash':
            if code or url or not amount:
                raise ValidationError('For cash payment specify amount only')
            data['metadata'] = {'type': _type, 'amount': float(amount.amount)}
            return data
        if _type == 'card':
            if amount or (not code and not url):
                raise ValidationError('For card payment use "code" and "url" fields')
            data['metadata'] = {'type': _type, 'code': code, 'url': url}
            return data
        raise ValidationError('Unknown payment type')


class PaidBillsListFilter(admin.SimpleListFilter):
    title = 'Payment'

    parameter_name = 'payment'

    def lookups(self, request, model_admin):
        return (
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return getattr(queryset.model.objects, value)()
        return queryset


class PaymentTodayListFilter(admin.SimpleListFilter):
    title = 'Pay date is today'

    parameter_name = 'payment_today'

    def lookups(self, request, model_admin):
        return (1, 'Must be paid today'),

    def queryset(self, request, queryset):
        if self.value():
            return queryset.model.objects.must_be_paid_today()
        return queryset


class PaymentTypeListFilter(admin.SimpleListFilter):
    title = 'Payment type'

    parameter_name = 'payment_type'

    def lookups(self, request, model_admin):
        return (
            ('paid_by_cash', 'With cash'),
            ('paid_online', 'Online'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return getattr(queryset.model.objects, value)()
        return queryset


class BillAdmin(SimpleHistoryAdmin):
    form = BillChangeAdminForm
    list_display = ('uuid', 'amount', 'due', 'paid_at', 'user', 'payment_type')
    list_filter = (PaidBillsListFilter, PaymentTodayListFilter, PaymentTypeListFilter)
    readonly_fields = ('user',)

    def save_model(self, request, obj, form, change):
        obj.metadata = form.cleaned_data.get('metadata')
        obj.user = request.user
        super().save_model(request, obj, form, change)


class PaidBillsInline(admin.TabularInline):
    model = Bill
    extra = 0

    def get_queryset(self, request):
        return self.model.objects.paid()


class UnpaidBillsInline(admin.TabularInline):
    model = Bill
    extra = 0

    def get_queryset(self, request):
        return self.model.objects.unpaid()


class BillsUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('nickname', 'email', 'blocked', 'is_superuser', 'note')}),
    )
    add_fieldsets = (
        (None, {'fields': ('nickname', 'email', 'blocked', 'is_superuser', 'password1', 'password2')}),
    )
    ordering = ('nickname',)
    list_display = ('nickname', 'blocked')
    list_filter = ('blocked',)
    search_fields = ('nickname',)
    ordering = ('nickname',)
    inlines = [PaidBillsInline, UnpaidBillsInline]


admin.site.register(Bill, BillAdmin)
admin.site.register(User, BillsUserAdmin)
