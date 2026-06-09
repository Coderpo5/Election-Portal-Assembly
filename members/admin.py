from django.contrib import admin
from .models import Party, Constituency, Candidate, RoundResult




@admin.register(Constituency)
class ConstituencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'number', 'name', 'incumbent_party', 'current_round', 'total_rounds',)
    ordering = ('number',)
    search_fields = ('name',)
    actions = ['reset_rounds', 'mark_completed']

    def reset_rounds(self, request, queryset):
        queryset.update(current_round=0)
    reset_rounds.short_description = "Reset current round to 0"

    def mark_completed(self, request, queryset):
        queryset.update(result_declared=True)
    mark_completed.short_description = "Mark result as declared"
    

class RoundResultInline(admin.TabularInline):
    model = RoundResult
    extra = 0

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'party', 'votes', 'constituency', 'current_round', 'total_rounds',)
    ordering = ('constituency__number', 'sno')
    list_filter = ('party', 'constituency')
    search_fields = ('name', 'party__name', 'constituency__name')
    inlines = [RoundResultInline]
    def current_round(self, obj):
        return obj.constituency.current_round
    current_round.short_description = "Current Round"

    def total_rounds(self, obj):
        return obj.constituency.total_rounds
    total_rounds.short_description = "Total Rounds"

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'color', 'type')
    search_fields = ('name', 'type' )

