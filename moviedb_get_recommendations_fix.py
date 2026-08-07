"""
Paste/replace get_recommendations in: backend/apps/ratings/views.py

Adjust imports / auth decorator names to match your existing views.py
(e.g. @token_required, get_user_from_token, Rating model field names).
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.movies.models import Movie
from apps.ratings.models import Rating


def _genre_overlap(source_genres, candidate_genres):
    """Return (overlap_count, has_any_overlap)."""
    source = set(source_genres or [])
    candidate = set(candidate_genres or [])
    if not source:
        return 0, False
    overlap = source & candidate
    return len(overlap), len(overlap) > 0


def _build_recommendation(candidate, score, source, source_movie, user_rating=None):
    rec = {
        '_id': str(candidate.id),
        'title': candidate.title,
        'year': candidate.year,
        'rating': candidate.rating,
        'genre': candidate.genre if isinstance(candidate.genre, list) else list(candidate.genre or []),
        'description': candidate.description,
        'popularity': candidate.popularity,
        'type': candidate.type,
        'score': round(score, 4),
        'source': source,  # 'rated' | 'watched'
        'sourceMovie': source_movie.title,
    }
    if source == 'rated' and user_rating is not None:
        rec['userRating'] = user_rating
    return rec


@csrf_exempt
@require_http_methods(["GET"])
def get_recommendations(request):
    """
    GET /api/ratings/recommendations/user
    Personalized recommendations from ratings + watched history.
    """
    try:
        # --- Auth: match whatever your ratings views already use ---
        # Example patterns seen in these challenges:
        #   user = request.user
        #   user = getattr(request, 'user_obj', None)
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', True):
            # Some challenges attach user via custom middleware after Bearer parse
            user = getattr(request, 'user_obj', None)
        if user is None:
            return JsonResponse({'message': 'Unauthorized'}, status=401)

        user_ratings = list(Rating.objects.filter(user=user).select_related('movie'))

        # Split signals: rated takes precedence over watched-only for same movie
        rated_entries = []      # Rating rows that have a numeric rating
        watched_only = []       # watched=True and no rating (or rating is None)

        rated_movie_ids = set()
        watched_movie_ids = set()

        for entry in user_ratings:
            mid = entry.movie_id
            if getattr(entry, 'watched', False):
                watched_movie_ids.add(mid)
            if entry.rating is not None:
                rated_entries.append(entry)
                rated_movie_ids.add(mid)

        for entry in user_ratings:
            if getattr(entry, 'watched', False) and entry.movie_id not in rated_movie_ids:
                watched_only.append(entry)

        if not rated_entries and not watched_only:
            return JsonResponse({
                'message': 'Start exploring movies by rating them or marking them as watched',
                'recommendations': [],
            }, status=200)

        exclude_ids = rated_movie_ids | watched_movie_ids

        # Candidates: rating >= 7.0, not already interacted with
        candidates = list(
            Movie.objects.filter(rating__gte=7.0).exclude(id__in=exclude_ids)
        )

        # movie_id -> best recommendation dict (keep higher score; rated > watched)
        best = {}

        def consider(candidate, score, source, source_movie, user_rating=None):
            key = str(candidate.id)
            rec = _build_recommendation(candidate, score, source, source_movie, user_rating)
            if key not in best:
                best[key] = rec
                return
            existing = best[key]
            # Prefer higher score; on tie prefer 'rated' over 'watched'
            if rec['score'] > existing['score']:
                best[key] = rec
            elif rec['score'] == existing['score'] and source == 'rated' and existing['source'] == 'watched':
                best[key] = rec

        # --- From RATED movies ---
        for entry in rated_entries:
            source_movie = entry.movie
            user_rating = entry.rating
            source_genres = source_movie.genre or []
            high = user_rating > 5  # strictly above 5

            for candidate in candidates:
                cand_genres = candidate.genre or []
                overlap_count, has_overlap = _genre_overlap(source_genres, cand_genres)
                rating_score = float(candidate.rating) / 10.0

                if high:
                    # Similar genres with 1.2x boost
                    if not has_overlap:
                        continue
                    genre_score = overlap_count / len(source_genres) if source_genres else 0.0
                    multiplier = 1.2
                    score = (genre_score * 0.7 + rating_score * 0.3) * multiplier
                    consider(candidate, score, 'rated', source_movie, user_rating)
                else:
                    # Low rating: DIFFERENT genres only; score = ratingScore
                    if has_overlap:
                        continue
                    score = rating_score
                    consider(candidate, score, 'rated', source_movie, user_rating)

        # --- From WATCHED-ONLY movies (no rating) ---
        for entry in watched_only:
            source_movie = entry.movie
            source_genres = source_movie.genre or []

            for candidate in candidates:
                cand_genres = candidate.genre or []
                overlap_count, has_overlap = _genre_overlap(source_genres, cand_genres)
                if not has_overlap:
                    continue
                rating_score = float(candidate.rating) / 10.0
                genre_score = overlap_count / len(source_genres) if source_genres else 0.0
                # No boost for watched-only
                score = (genre_score * 0.7 + rating_score * 0.3) * 1.0
                consider(candidate, score, 'watched', source_movie, user_rating=None)

        recommendations = sorted(best.values(), key=lambda r: r['score'], reverse=True)[:10]

        if not recommendations:
            return JsonResponse({
                'message': 'No recommendations found. Try rating more movies or exploring different genres',
                'recommendations': [],
            }, status=200)

        return JsonResponse({
            'message': f'Found {len(recommendations)} personalized recommendations',
            'recommendations': recommendations,
        }, status=200)

    except Exception as e:
        print(f'Get recommendations error: {e}')
        import traceback
        traceback.print_exc()
        return JsonResponse({'message': 'Server error'}, status=500)
