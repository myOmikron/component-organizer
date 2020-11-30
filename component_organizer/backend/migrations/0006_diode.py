# Generated by Django 3.1.3 on 2020-11-30 08:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_transformer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Diode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schematic_symbol_path', models.CharField(blank=True, default='', max_length=1024)),
                ('datasheet_path', models.CharField(blank=True, default='', max_length=1024)),
                ('mounting', models.CharField(choices=[('THT', 'THT'), ('SMD', 'SMD'), ('Other', 'Other')], default='THT', max_length=255)),
                ('name', models.CharField(default='', max_length=255)),
                ('voltage_drop', models.FloatField(default=0)),
                ('breakdown_voltage', models.FloatField(default=0)),
                ('diode_type', models.CharField(choices=[('rectifier', 'rectifier'), ('schottky', 'schottky'), ('zener', 'zener'), ('led', 'led'), ('photo diode', 'photodiode'), ('laser diode', 'laserdiode'), ('tunnel diode', 'tunneldiode'), ('backward diode', 'backwarddiode'), ('avalanche diode', 'avalanchediode'), ('TVS diode', 'tvsdioide'), ('constant current diode', 'constantcurrentdiode'), ('vacuum diode', 'vacuumdiode'), ('step recovery diode', 'steprecoverydiode')], default='rectifier', max_length=255)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.category')),
                ('custom_values', models.ManyToManyField(blank=True, to='backend.KeyValuePair')),
                ('locations', models.ManyToManyField(blank=True, to='backend.ItemLocationModel')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]