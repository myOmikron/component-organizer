# Generated by Django 4.0 on 2021-12-27 12:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('backend', '0007_remove_unitvalue_expo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemtemplate',
            name='fields',
        ),
        migrations.CreateModel(
            name='ItemTemplateField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.stringvalue')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.itemtemplate')),
                ('value_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
        ),
    ]
