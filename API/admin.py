from django.contrib import admin

from .models import Project, NodeType, RuleType, Node, NodeRule


class NodeRuleInline(admin.TabularInline):
    model = NodeRule
    fk_name = 'node'
    extra = 1


class NodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'content', 'node_type',)
    search_fields = ('content',)
    inlines = [NodeRuleInline, ]


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner',)
    search_fields = ('name',)


class NodeTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color',)
    search_fields = ('name',)


class RuleTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code',)
    search_fields = ('name',)


admin.site.register(Project, ProjectAdmin)
admin.site.register(NodeType, NodeTypeAdmin)
admin.site.register(RuleType, RuleTypeAdmin)
admin.site.register(Node, NodeAdmin)
