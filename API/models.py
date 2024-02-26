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

    def __str__(self):
        return self.name


class NodeType(models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name='ID'
    )
    name = models.CharField(
        max_length=60,
        verbose_name='Название'
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

    class Meta:
        verbose_name = 'Узел'
        verbose_name_plural = 'Узлы'

    def __str__(self):
        return self.content[:50] + '...' if len(self.content) > 50 else self.content


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
