import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('garden', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('date', models.DateField()),
                ('recurrence', models.CharField(
                    choices=[('once', 'Once'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
                    default='once',
                    max_length=20,
                )),
                ('event_type', models.CharField(
                    choices=[('watering', 'Watering'), ('fertilizing', 'Fertilizing'), ('pruning', 'Pruning'), ('other', 'Other')],
                    default='other',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='events',
                    to='garden.gardenitem',
                )),
            ],
            options={
                'ordering': ['date'],
            },
        ),
    ]
