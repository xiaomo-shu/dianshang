# Generated by Django 2.1 on 2020-02-27 09:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web_manage', '0007_auto_20200226_1815'),
    ]

    operations = [
        migrations.CreateModel(
            name='YzyInterfaceIp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=64, unique=True)),
                ('ip', models.CharField(max_length=32)),
                ('netmask', models.CharField(max_length=32)),
                ('is_image', models.IntegerField(default=0)),
                ('is_manage', models.IntegerField(default=0)),
                ('type', models.IntegerField(default=0)),
                ('status', models.IntegerField(default=0)),
                ('deleted', models.IntegerField(default=0)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'yzy_interface_ip',
                'ordering': ['id'],
            },
        ),
        migrations.AlterField(
            model_name='yzybaseimages',
            name='path',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='yzynodenetworkinfo',
            name='node',
            field=models.ForeignKey(db_column='node_uuid', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='yzy_node_interfaces', to='web_manage.YzyNodes', to_field='uuid'),
        ),
        migrations.AddField(
            model_name='yzyinterfaceip',
            name='interface',
            field=models.ForeignKey(db_column='interface_uuid', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='yzy_interface_ips', to='web_manage.YzyNodeNetworkInfo', to_field='uuid'),
        ),
    ]