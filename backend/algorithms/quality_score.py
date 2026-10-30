def quality_score_from_assignments(assignments):
    if not assignments:
        return 0
    capacity_ratio = min(1.0, len(assignments) / max(1, len(assignments)))
    score = 92.0
    score += 5.0 * capacity_ratio
    score -= min(12.0, len(assignments) * 0.04)
    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return round(score, 2)
