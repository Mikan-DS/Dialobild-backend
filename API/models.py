import typing

from colorfield.fields import ColorField
# from django.contrib.auth.models import User
from users.models import User
from django.core.validators import RegexValidator
from django.db import models


class Project(models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=60,
        verbose_name='Название'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец',
        related_name='projects'
    )

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'

        unique_together = ('name', 'owner')

    def __str__(self):
        return self.name

    def get_avalaible_rule_types(self):
        return RuleType.objects.all()

    def get_avalaible_node_types(self):
        return NodeType.objects.all()

    @property
    def nodes_json_format(self):
        return list(map(lambda node: node.get_js_format(), self.nodes.all()))

    @property
    def node_types_json_format(self):
        return list(map(lambda node_type: node_type.get_js_format(), self.get_avalaible_node_types()))

    @property
    def rule_types_json_format(self):
        return list(map(lambda rule_type: rule_type.get_js_format(), self.get_avalaible_rule_types()))

class NodeType(models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=60,
        verbose_name='Название'
    )

    code = models.SlugField(
        max_length=60,
        verbose_name='Кодовое обозначение',
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z]+$',
                message='Кодовое обозначение должно быть на латинице и без пробелов',
            ),
        ]
    )

    color = ColorField(
        max_length=9,
        verbose_name='Цвет'
    )

    class Meta:
        verbose_name = 'Тип узла'
        verbose_name_plural = 'Типы узлов'

    def __str__(self):
        return self.name

    def get_js_format(self) -> dict:

        return {
            'code': self.code,
            'name': self.name,
            'color': self.color
        }

class RuleType(models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=60,
        verbose_name='Название'
    )

    code = models.SlugField(
        max_length=60,
        verbose_name='Кодовое обозначение',
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-zA-Z]+$',
                message='Кодовое обозначение должно быть на латинице и без пробелов',
            ),
        ]
    )

    class Meta:
        verbose_name = 'Тип правила'
        verbose_name_plural = 'Типы правил'

    def __str__(self):
        return self.name

    def get_js_format(self) -> dict:
        return {
            'code': self.code,
            'name': self.name
        }


class Node(models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    content = models.TextField(
        verbose_name='Контент'
    )
    node_type = models.ForeignKey(
        NodeType,
        on_delete=models.CASCADE,
        verbose_name='Тип узла',
        related_name='nodes'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        verbose_name='Проект',
        related_name='nodes'
    )

    x = models.IntegerField(
        verbose_name='Х позиция (столбец)',
        default=0,
    )

    y = models.IntegerField(
        verbose_name='Y позиция (строка',
        default=0,
    )

    class Meta:
        verbose_name = 'Узел'
        verbose_name_plural = 'Узлы'

    def __str__(self):
        return self.content[:50] + '...' if len(self.content) > 50 else self.content


    def get_js_format(self) -> dict:

        rules: typing.Dict[str, typing.List] = dict(map(lambda rule_type: (rule_type.code, []), self.project.get_avalaible_rule_types()))

        for rule in self.node_rules.all():
            rules[rule.rule.code].append(
                rule.connected_node.id
            )

        return {
            'nodeType': self.node_type.code,
            'content': self.content,
            'location': self.location,
            'id': self.id,
            'rules': rules,
        }

    @property
    def location(self):
        return {'x': self.x, 'y': self.y}


class NodeRule(models.Model):
    node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='Узел',
        related_name='node_rules'
    )
    rule = models.ForeignKey(
        RuleType,
        on_delete=models.CASCADE,
        verbose_name='Правило',
        related_name='node_rules'
    )
    connected_node = models.ForeignKey(
        Node,
        on_delete=models.CASCADE,
        verbose_name='Подключенный узел',
        related_name='connected_node_rules'
    )

    class Meta:
        verbose_name = 'Правило в узле'
        verbose_name_plural = 'Правила в узлах'

    def __str__(self):
        return f"{self.node} - {self.rule} - {self.connected_node}"
