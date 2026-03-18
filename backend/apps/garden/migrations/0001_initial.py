from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GardenItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('type', models.CharField(
                    choices=[('plant', 'Plant'), ('tree', 'Tree'), ('shrub', 'Shrub'), ('other', 'Other')],
                    default='plant',
                    max_length=20,
                )),
                ('description', models.TextField(blank=True)),
                ('cares', models.TextField(blank=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='garden/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
