import re
from datetime import date, timedelta
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CalendarEvent
from .serializers import CalendarEventSerializer


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.select_related('item').all()
    serializer_class = CalendarEventSerializer
    filterset_fields = ['event_type', 'recurrence', 'item']
    ordering_fields = ['date', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        week = self.request.query_params.get('week')
        month = self.request.query_params.get('month')
        if week:
            match = re.match(r'(\d{4})-W(\d{2})', week)
            if match:
                year, week_num = int(match.group(1)), int(match.group(2))
                start = date.fromisocalendar(year, week_num, 1)
                end = start + timedelta(days=6)
                qs = qs.filter(date__range=[start, end])
        elif month:
            match = re.match(r'(\d{4})-(\d{2})', month)
            if match:
                year, month_num = int(match.group(1)), int(match.group(2))
                qs = qs.filter(date__year=year, date__month=month_num)
        return qs

    @action(detail=False, methods=['get'], url_path='by-item/(?P<item_id>[^/.]+)')
    def by_item(self, request, item_id=None):
        events = self.get_queryset().filter(item_id=item_id)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)
