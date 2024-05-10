# Generated by Django 4.2.13 on 2024-05-10 12:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False, unique=True)),
                ('path', models.CharField(max_length=100)),
                ('type', models.IntegerField(choices=[(1, 'Model'), (2, 'Photo')])),
            ],
        ),
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False, unique=True)),
                ('type', models.IntegerField(choices=[(1, 'Tag'), (2, 'Culture'), (3, 'Form')])),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='PiezaArq',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False, unique=True)),
                ('description', models.CharField(max_length=300)),
                ('preview', models.CharField(max_length=100)),
                ('culture', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cultures', to='piezas.metadata')),
                ('form', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forms', to='piezas.metadata')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='models_3d', to='piezas.metadata')),
                ('photos', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='piezas.media')),
                ('tags', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='piezas.metadata')),
            ],
        ),
    ]