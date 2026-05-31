from app.database import SessionLocal
from app.services.pillar_service import PillarService
import json

db = SessionLocal()
out = []
for y in (2025, 2024):
    ps = PillarService.get_pillar_score(db, 'E', y)
    evo = PillarService.get_monthly_scores(db, y)
    s = evo.series['E']
    avg = round(sum(s) / len(s), 2) if s else 0
    out.append({'year': y, 'score': ps.score, 'monthly_avg': avg, 'series': s})

with open('out_scores.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

db.close()
print('wrote out_scores.json')
