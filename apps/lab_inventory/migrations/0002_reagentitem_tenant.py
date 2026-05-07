"""
Add organization (tenant) field to ReagentItem.
Populates existing rows from their parent reagent's organization.
"""
from django.db import migrations, models
import django.db.models.deletion


def populate_organization(apps, schema_editor):
    """Set organization from parent reagent for existing ReagentItems."""
    ReagentItem = apps.get_model('lab_inventory', 'ReagentItem')
    for item in ReagentItem.objects.select_related('reagent').all():
        item.organization = item.reagent.organization
        item.save(update_fields=['organization'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_user_org_constraint'),
        ('lab_inventory', '0001_initial'),
    ]

    operations = [
        # 1. Add nullable organization FK
        migrations.AddField(
            model_name='reagentitem',
            name='organization',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='core.organization',
                verbose_name='organización',
            ),
        ),
        # 2. Populate from parent reagent
        migrations.RunPython(populate_organization, migrations.RunPython.noop),
        # 3. Make non-nullable
        migrations.AlterField(
            model_name='reagentitem',
            name='organization',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='core.organization',
                verbose_name='organización',
            ),
        ),
        # 4. Add unique constraint
        migrations.AddConstraint(
            model_name='reagentitem',
            constraint=models.UniqueConstraint(
                fields=['reagent', 'supply'],
                name='unique_reagent_supply_item',
            ),
        ),
    ]
