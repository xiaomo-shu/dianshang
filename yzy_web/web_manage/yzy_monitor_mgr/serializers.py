from web_manage.common.utils import DateTimeFieldMix
from .models import *


class YzyNodesSerializer2(DateTimeFieldMix):

    class Meta:
        model = YzyNodes2
        # fields = '__all__'
        fields = ('name', 'uuid', 'hostname', 'ip', 'status', 'type', 'created_at')