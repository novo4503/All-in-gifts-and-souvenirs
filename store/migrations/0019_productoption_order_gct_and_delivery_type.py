from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0018_category_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('values', models.JSONField(blank=True, default=list)),
                ('is_required', models.BooleanField(default=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='store.product')),
            ],
            options={
                'ordering': ('name',),
                'unique_together': {('product', 'name')},
            },
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_type',
            field=models.CharField(default='island', max_length=30),
        ),
        migrations.AddField(
            model_name='order',
            name='gct_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
