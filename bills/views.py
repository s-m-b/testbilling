from rest_framework import viewsets, mixins, exceptions
from .serialisers import BillSerializer
from .models import Bill


class BillViewSet(mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        amount = float(serializer.data.get('amount') or 0)
        if amount > 2400:
            request.user.note += f'Tried to add bill with amount {amount}\n'
            request.user.save()
            raise exceptions.ValidationError('Bill with amount over 2400 is not acceptable')
        super().create(request, *args, **kwargs)