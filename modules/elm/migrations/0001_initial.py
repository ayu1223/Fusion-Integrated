from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('modules/directory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=models.CASCADE, to='modules/directory.userref')),
            ],
            options={
                'db_table': 'elm_leave_request',
                'indexes': [
                    models.Index(fields=['user'], name='leave_request_user_idx'),
                ],
            },
        ),
    ]
