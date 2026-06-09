from django.db import models
from colorfield.fields import ColorField
from django.db.models import Sum


class Constituency(models.Model):
    number = models.IntegerField(default=0)
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    party_name = models.CharField(max_length=100, blank=True)
    incumbent_party = models.CharField(max_length=20, default='')
    current_round = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=0)
    result_declared = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Party(models.Model):
    name = models.CharField(max_length=100)
    acronym = models.CharField(max_length=20)
    color = ColorField(default="#FFFFFF")
    constituencies = models.ManyToManyField(
        'Constituency',
        blank=True,
        related_name='parties_with_most_votes'
    )
    TYPE_CHOICES = [
        ('national', 'National'),
        ('state', 'State'),
        ('unrecognised', 'Unrecognised'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='state'
    )

    def __str__(self):
        return self.name


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    sno = models.IntegerField(default=0)
    gender = models.CharField(max_length=10, default='')
    party = models.ForeignKey(
        Party,
        related_name='candidates',
        on_delete=models.CASCADE
    )
    constituency = models.ForeignKey(
        Constituency,
        related_name='candidates',
        on_delete=models.CASCADE
    )
    postal_votes = models.IntegerField(default=0)

    @property
    def votes(self):
        return (
            self.round_results.aggregate(
                total=Sum('round_votes')
            )['total']
            or 0
        )

    def cumulative_votes_upto(self, round_number):
        return (
            self.round_results.filter(
                round_number__lte=round_number
            ).aggregate(
                total=Sum('round_votes')
            )['total']
            or 0
        )

    def __str__(self):
        return self.name


class RoundResult(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        related_name='round_results',
        on_delete=models.CASCADE
    )

    round_number = models.PositiveIntegerField()

    round_votes = models.PositiveIntegerField(default=0)

    cumulative_votes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (
            'candidate',
            'round_number'
        )
        ordering = ['round_number']

    def __str__(self):
        return (
            f"{self.candidate.name} - "
            f"Round {self.round_number}"
        )