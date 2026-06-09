from django.shortcuts import render, redirect
from django.http import JsonResponse
from math import ceil

from urllib3 import request
from .models import Party, Constituency, Candidate, RoundResult
from django.db.models import Sum, F
from collections import defaultdict
from django.conf import settings
import os
from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Coalesce

def home(request):

    constituencies = Constituency.objects.all()
    candidates = Candidate.objects.all()

    parties = Party.objects.all()
    party_data = []
    tot_leading_count = 0
    tot_won_count = 0

    for constituency in constituencies:
        top_candidate = Candidate.objects.filter(constituency=constituency).annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    ).order_by('-total_votes').first()
        if top_candidate and top_candidate.votes + top_candidate.postal_votes > 0:
            for candidate in candidates:
                if top_candidate.name == candidate.name:
                    party_name = candidate.party
                    party_name.constituencies.add(constituency)
                    constituency.party_name = party_name
        else:
            constituency.party_name = Party.objects.get(name = "No Result")
                

    for party in parties:
        constituency_leading_count = 0
        constituency_won_count = 0
        for constituency in constituencies:
            if constituency.party_name:
                if(constituency.party_name.name == party.name and constituency.current_round <= constituency.total_rounds):
                    constituency_leading_count = constituency_leading_count+1
                elif(constituency.party_name.name == party.name and constituency.result_declared == True):
                    constituency_won_count = constituency_won_count+1
        if party != Party.objects.get(name = "No Result"):
            tot_leading_count = tot_leading_count+constituency_leading_count
            tot_won_count = tot_won_count+constituency_won_count
        party_data.append({
            'name': party.name,
            'acronym': party.acronym,
            'leading_count': constituency_leading_count,
            'won_count': constituency_won_count,
            'count': constituency_won_count+constituency_leading_count,
            'color': party.color,
        })
    party_data.sort(key=lambda x: x['count'], reverse=True)

    tot_count = tot_leading_count + tot_won_count

    return render(request, 'members/home.htm', {'party_data': party_data, 'tot_count': tot_count})

def index(request):
  constituencies = Constituency.objects.all()
  candidates = Candidate.objects.all()
  
  parties = Party.objects.all()
  party_data = []
  tot_leading_count = 0
  tot_won_count = 0

  for constituency in constituencies:
     top_candidate = Candidate.objects.filter(constituency=constituency).annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    ).order_by('-total_votes').first()
     if top_candidate and top_candidate.votes + top_candidate.postal_votes > 0:
        for candidate in candidates:
          if top_candidate.name == candidate.name:
              party_name = candidate.party
              party_name.constituencies.add(constituency)
              constituency.party_name = party_name
     else:
        constituency.party_name = Party.objects.get(name = "No Result")
              

  for party in parties:
        constituency_leading_count = 0
        constituency_won_count = 0
        for constituency in constituencies:
           if constituency.party_name:
            if(constituency.party_name.name == party.name and constituency.current_round <= constituency.total_rounds):
                constituency_leading_count = constituency_leading_count+1
            elif(constituency.party_name.name == party.name and constituency.result_declared == True):
                constituency_won_count = constituency_won_count+1
        if party != Party.objects.get(name = "No Result"):
          tot_leading_count = tot_leading_count+constituency_leading_count
          tot_won_count = tot_won_count+constituency_won_count
        party_data.append({
            'name': party.name,
            'acronym': party.acronym,
            'leading_count': constituency_leading_count,
            'won_count': constituency_won_count,
            'count': constituency_won_count+constituency_leading_count,
            'color': party.color,
        })
  tot_count = tot_leading_count + tot_won_count
  party_data.sort(key=lambda x: x['count'], reverse=True)
  top_six_count = 0
  processed = 0

  for party in party_data:
    if party['name'] == "No Result":
        continue

    print(party['count'], party['name'])
    top_six_count += party['count']
    processed += 1

    if processed == 6:
        break

  not_top_six_count = tot_count - top_six_count
  constituencies = constituencies.order_by('number')
             
  return render(request, 'members/index.htm', {'constituencies': constituencies, 'party_data': party_data, 'tot_leading_count': tot_leading_count, 'tot_won_count': tot_won_count, 'tot_count': tot_count, 'not_top_six_count': not_top_six_count})

def candidate_wise(request, constituency_id):
  constituency = Constituency.objects.get(id = constituency_id)
  incumbent_party = constituency.incumbent_party
  candidates = Candidate.objects.filter(constituency=constituency).annotate(
    custom_order=Case(
        When(name="NOTA", then=Value(1)),  # Assign a higher value to the specific candidate
        default=Value(0),  # Assign a lower value to all others
        output_field=IntegerField(),
    )
    ).annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    ).order_by('custom_order', '-total_votes')
  vote_difference = candidates[0].votes + candidates[0].postal_votes - candidates[1].votes - candidates[1].postal_votes if len(candidates) > 1 else None
  candidate_data = []
  for candidate in candidates:
     vote_diff = candidates[0].votes + candidates[0].postal_votes - candidate.votes - candidate.postal_votes if len(candidates) > 1 else None
     candidate_data.append({
        'name': candidate.name,
        'gender': candidate.gender,
        'party': candidate.party,
        'acronym': candidate.party.acronym,
        'color': candidate.party.color,
        'votes': candidate.votes + candidate.postal_votes,
        'vote_diff': vote_diff
     })
  top_candidate = candidate_data[0]
  acronym = top_candidate['acronym']
  color = top_candidate['color']
  return render(request, 'members/candidate-wise.htm', {'incumbent_party': incumbent_party, 'constituency': constituency, 'candidates': candidates, 'vote_difference': vote_difference, 'candidate_data': candidate_data, 'top_candidate': top_candidate, 'acronym': acronym, 'color': color,})

def votes(request, constituency_id):
  constituency = Constituency.objects.get(id = constituency_id)
  incumbent_party = constituency.incumbent_party
  candidates = Candidate.objects.filter(constituency=constituency).annotate(
    custom_order=Case(
        When(name="NOTA", then=Value(1)),  # Assign a higher value to the specific candidate
        default=Value(0),  # Assign a lower value to all others
        output_field=IntegerField(),
    )
    ).order_by('custom_order', 'sno')
  tot_votes = 0
  tot_postal_votes = 0
  tot_overall_votes = 0
  candidate_data = []
  for candidate in candidates:
     tot_votes = tot_votes + candidate.votes
     tot_postal_votes = tot_postal_votes + candidate.postal_votes
     tot_overall_votes = tot_overall_votes + candidate.votes + candidate.postal_votes

  for candidate in candidates:
     percentage = ((candidate.votes + candidate.postal_votes) / tot_votes) * 100 if tot_votes > 0 else 0
     candidate_data.append({
        'name': candidate.name,
        'party': candidate.party,
        'acronym': candidate.party.acronym,
        'color': candidate.party.color,
        'votes': candidate.votes,
        'postal_votes': candidate.postal_votes,
        'total_votes': candidate.votes + candidate.postal_votes,
        'percentage': round(percentage, 2),
     })
  top_candidate = sorted(candidate_data, key=lambda x: x['total_votes'], reverse=True)[0]
  acronym = top_candidate['acronym']
  color = top_candidate['color']
  return render(request, 'members/votes.htm', {'incumbent_party': incumbent_party, 'constituency': constituency, 'candidates': candidates, 'tot_votes': tot_votes, 'tot_postal_votes': tot_postal_votes, 'tot_overall_votes': tot_overall_votes, 'candidate_data': candidate_data, 'top_candidate': top_candidate, 'acronym': acronym, 'color': color,})


def party(request, party_acronym):
  party = Party.objects.get(acronym = party_acronym)
  constituencies = Constituency.objects.all()
  constituency_data = []
  for constituency in constituencies:
     candidates = Candidate.objects.filter(constituency = constituency).annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    ).order_by('-total_votes')
     top_candidate = candidates[0]
     con = top_candidate.constituency
     vote_difference = candidates[0].votes + candidates[0].postal_votes - candidates[1].votes - candidates[1].postal_votes if len(candidates) > 1 else None
     if top_candidate.party.name == party.name and con.result_declared == True:
        constituency_data.append({
           'name': con.name,
           'id': con.id,
           'number': con.number,
           'candidate': candidates[0],
           'votes': candidates[0].votes + candidates[0].postal_votes,
           'margin': vote_difference,
           'current_round': con.current_round,
           'total_rounds': con.total_rounds
        })

  constituency_data.sort(key=lambda x: x['number'], reverse=False)
  return render(request, 'members/party.htm', {'party': party, 'constituencies': constituencies, 'vote_difference': vote_difference, 'constituency_data': constituency_data,})

def partyLeads(request, party_acronym):
  party = Party.objects.get(acronym = party_acronym)
  constituencies = Constituency.objects.all()
  constituency_data = []
  for constituency in constituencies:
     candidates = Candidate.objects.filter(constituency = constituency).annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    ).order_by('-total_votes')
     top_candidate = candidates[0]
     con = top_candidate.constituency
     vote_difference = candidates[0].votes + candidates[0].postal_votes - candidates[1].votes - candidates[1].postal_votes if len(candidates) > 1 else None
     if top_candidate.party.name == party.name and con.current_round <= con.total_rounds and candidates[0].votes!=0:
        constituency_data.append({
           'name': con.name,
           'id': con.id,
           'number': con.number,
           'candidate': candidates[0],
           'votes': candidates[0].votes + candidates[0].postal_votes,
           'margin': vote_difference,
           'current_round': con.current_round,
           'total_rounds': con.total_rounds
        })

  constituency_data.sort(key=lambda x: x['number'], reverse=False)
  return render(request, 'members/party_leads.htm', {'party': party, 'constituencies': constituencies, 'vote_difference': vote_difference, 'constituency_data': constituency_data,})


def constituency_data(request):
  constituencies = Constituency.objects.all()
  data = []
  candidates = Candidate.objects.all()
  party_colors = {}  # Store party color information
  party_win_count = defaultdict(int)
  for constituency in constituencies:
    top_candidate = Candidate.objects.filter(constituency=constituency).annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    ).order_by('-total_votes').first()
    if top_candidate:
          if top_candidate.votes + top_candidate.postal_votes > 0:
              party_name = top_candidate.party
          else:
              party_name = Party.objects.get(name="No Result")
          
          # Add data for the constituency
          data.append({
              'number': constituency.number,
              'id': constituency.id,
              'ac_name': constituency.name,
              'candidate_name': top_candidate.name if (top_candidate.votes + top_candidate.postal_votes) > 0 else "NIL",
              'party_name': party_name.name,
              'party_acronym': party_name.acronym,              
          })
          if(party_name.acronym!="NR"):
            party_win_count[party_name.acronym] += 1
  
  sorted_party_win_count = sorted(party_win_count.items(), key = lambda item: item[1], reverse=True)
  top_parties = sorted_party_win_count[:10]

  other_parties_count = sum([count for _, count in sorted_party_win_count[10:]])

  if other_parties_count > 0:
      top_parties.append(('Others', other_parties_count))

  party_vote_data = []
  parties = Party.objects.all()
  for party in parties:
      round_votes = (
        RoundResult.objects
        .filter(candidate__party=party)
        .aggregate(total=Sum('round_votes'))
      )['total'] or 0

      postal_votes = (Candidate.objects.filter(party=party).aggregate(total=Sum('postal_votes')))['total'] or 0
      total_votes = round_votes + postal_votes
      party_vote_data.append({
          'party_acronym': party.acronym,
          'party_type': party.type,
          'total_votes': total_votes,
      })

  party_colors2 = []
  for party in parties:
     party_colors2.append({
        'party_acronym': party.acronym,
        'color': party.color
     })

  party_vote_data.sort(key=lambda x: x['party_acronym'], reverse=False)

  party_colors = {party["party_acronym"]: party["color"] for party in party_colors2}


  # Combine both data
  response_data = {
      'constituency_data': data,
      'party_vote_data': party_vote_data,
      'party_colors': party_colors,
      'party_win_count': dict(top_parties),
  }

  return JsonResponse(response_data, safe=False)


def statewise(request, set_number):
    set_number = int(set_number)

    parties = list(Party.objects.all())

    candidates = (
        Candidate.objects
        .select_related('party', 'constituency')
        .annotate(
        total_votes=Coalesce(Sum('round_results__round_votes'), 0) + F('postal_votes')
    )
        .order_by('constituency_id', '-total_votes')
    )

    candidates_by_constituency = defaultdict(list)

    for candidate in candidates:
        candidates_by_constituency[
            candidate.constituency_id
        ].append(candidate)

    party_stats = {
        party.name: {
            'name': party.name,
            'acronym': party.acronym,
            'leading_count': 0,
            'won_count': 0,
        }
        for party in parties
    }

    result_constituencies = []

    tot_leading_count = 0
    tot_won_count = 0

    all_constituencies = list(
        Constituency.objects.all().order_by('name')
    )

    for constituency in all_constituencies:
        constituency_candidates = candidates_by_constituency.get(
            constituency.id,
            []
        )

        top_candidate = (
            constituency_candidates[0]
            if constituency_candidates
            else None
        )

        if not top_candidate:
            continue

        top_votes = top_candidate.total_votes or 0

        if top_votes <= 0:
            continue

        result_constituencies.append(constituency)

        party_name = top_candidate.party.name

        if constituency.result_declared:
            party_stats[party_name]['won_count'] += 1

            if party_name != "No Result":
                tot_won_count += 1
        else:
            party_stats[party_name]['leading_count'] += 1

            if party_name != "No Result":
                tot_leading_count += 1

    total_results = len(result_constituencies)

    total_pages = max(
        1,
        ceil(total_results / 20)
    )

    start_index = (set_number - 1) * 20
    end_index = start_index + 20

    constituencies = result_constituencies[
        start_index:end_index
    ]

    party_data = []

    for stats in party_stats.values():
        stats['total_count'] = (
            stats['leading_count']
            + stats['won_count']
        )

        party_data.append(stats)

    party_data.sort(
        key=lambda x: x['total_count'],
        reverse=True
    )

    party_lookup = {
        party['name']: party
        for party in party_data
    }

    constituency_data = []

    for constituency in constituencies:
        constituency_candidates = candidates_by_constituency.get(
            constituency.id,
            []
        )

        top_candidate = constituency_candidates[0]

        second_candidate = (
            constituency_candidates[1]
            if len(constituency_candidates) > 1
            else None
        )

        top_votes = top_candidate.total_votes or 0

        second_votes = (
            second_candidate.total_votes or 0
            if second_candidate
            else 0
        )

        leading_party_name = top_candidate.party.name

        second_party_name = (
            second_candidate.party.name
            if second_candidate
            else "No Result"
        )

        leading_party_stats = party_lookup.get(
            leading_party_name,
            {
                'leading_count': 0,
                'won_count': 0,
            }
        )

        second_party_stats = party_lookup.get(
            second_party_name,
            {
                'leading_count': 0,
                'won_count': 0,
            }
        )

        constituency_data.append({
            'name': constituency.name,
            'number': constituency.number,

            'top_candidate': top_candidate.name,
            'party_name': leading_party_name,

            'second_candidate': (
                second_candidate.name
                if second_candidate
                else "No Result"
            ),

            'second_party': second_party_name,

            'current_round': constituency.current_round,
            'total_rounds': constituency.total_rounds,
            'result_declared': constituency.result_declared,

            'margin': top_votes - second_votes,

            'party_leading_count':
                leading_party_stats['leading_count'],

            'party_won_count':
                leading_party_stats['won_count'],

            'second_party_leading_count':
                second_party_stats['leading_count'],

            'second_party_won_count':
                second_party_stats['won_count'],
        })

    page_numbers = range(
        1,
        total_pages + 1
    )

    return render(
        request,
        'members/statewise.htm',
        {
            'constituency_data': constituency_data,
            'party_data': party_data,
            'tot_leading_count': tot_leading_count,
            'tot_won_count': tot_won_count,
            'tot_count': tot_leading_count + tot_won_count,
            'set_number': set_number,
            'page_numbers': page_numbers,
        },
    )

def roundwise(request, constituency_id):

    constituency = Constituency.objects.get(id=constituency_id)
    incumbent_party = constituency.incumbent_party

    candidates = Candidate.objects.filter(constituency=constituency)

    candidate_data = []

    # Pre-fetch all round results for this constituency
    round_results = RoundResult.objects.filter(
        candidate__constituency=constituency
    )

    round_map = defaultdict(lambda: defaultdict(int))

    for rr in round_results:
        print(rr.candidate_id, rr.round_number, rr.round_votes)
        round_map[rr.candidate_id][rr.round_number] = rr.round_votes

    for candidate in candidates:

        # votes in THIS round
        rounds_data=[]
        cumulative = 0


        for r in range(1, constituency.current_round + 1):
            previous_votes = cumulative
            round_votes = round_map[candidate.id].get(r, 0)
            cumulative += round_votes

            rounds_data.append({
                "round": r,
                "round_votes": round_votes,
                "cumulative_votes": cumulative,
                "previous_votes": previous_votes,
            })

        candidate_data.append({
            'name': candidate.name,
            'party': candidate.party,
            'acronym': candidate.party.acronym,
            'color': candidate.party.color,
            'rounds': rounds_data,
        })

    all_rounds_data = []

    for r in range(1, constituency.current_round + 1):
        round_info = {
            'round': r,
            'candidates': [],
            'round_total': 0,
            'overall_total': 0,
            'prev_total': 0
        }

        for candidate in candidates:
            round_votes = round_map[candidate.id].get(r, 0)
            prev_round_votes = 0
            for r1 in range(1, r):
                prev_round_votes += round_map[candidate.id].get(r1, 0)
            round_info['candidates'].append({
                'name': candidate.name,
                'party': candidate.party,
                'acronym': candidate.party.acronym,
                'color': candidate.party.color,
                'round_votes': round_votes,
                'previous_votes': prev_round_votes,
                'total_votes': prev_round_votes + round_votes,
            })
            round_info['prev_total'] += prev_round_votes
            round_info['round_total'] += round_votes
            round_info['overall_total'] += prev_round_votes + round_votes   

        all_rounds_data.append(round_info)

    rounds = list(range(1, constituency.total_rounds + 1))

    pages = [
        rounds[i:i+17]
        for i in range(0, len(rounds), 17)
    ]

    return render(
        request,
        'members/round-wise.htm',
        {
            'constituency': constituency,
            'incumbent_party': incumbent_party,
            'candidate_data': candidate_data,

            'pages': pages,
            'current_round': constituency.current_round,
            'total_rounds': constituency.total_rounds,
            'all_rounds_data': all_rounds_data,
        }
    )