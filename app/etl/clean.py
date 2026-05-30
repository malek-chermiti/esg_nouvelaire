from app.database import engine
from sqlalchemy import text


def run_etl():
    rapport = {}
    total = 0

    print("\n🚀 Démarrage ETL — Nettoyage des données sales\n")

    with engine.connect() as conn:

        # 1. aviation_license — license_number NULL ET aircraft_concerned NULL
        r = conn.execute(text("""
            SELECT id FROM aviation_license
            WHERE license_number IS NULL AND aircraft_concerned IS NULL
        """))
        ids = [row.id for row in r.fetchall()]
        for i in ids:
            print(f"🗑️  [aviation_license] id={i} → license_number et aircraft_concerned NULL")
        if ids:
            conn.execute(text(f"DELETE FROM aviation_license WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["aviation_license"] = len(ids)
        print(f"✅ [aviation_license] {len(ids)} ligne(s) supprimée(s)\n")

        # 2. payment_tracking — amount_tnd = 0
        r = conn.execute(text("""
            SELECT id, payment_mode, payment_date FROM payment_tracking
            WHERE amount_tnd = 0
        """))
        rows = r.fetchall()
        ids = [row.id for row in rows]
        for row in rows:
            print(f"🗑️  [payment_tracking] id={row.id} → {row.payment_mode} | amount = 0 | date={row.payment_date}")
        if ids:
            conn.execute(text(f"DELETE FROM payment_tracking WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["payment_tracking"] = len(ids)
        print(f"✅ [payment_tracking] {len(ids)} ligne(s) supprimée(s)\n")

        # 3. tax_obligation — amount_tnd = 0
        r = conn.execute(text("""
            SELECT id, tax_type, period_start FROM tax_obligation
            WHERE amount_tnd = 0
        """))
        rows = r.fetchall()
        ids = [row.id for row in rows]
        for row in rows:
            print(f"🗑️  [tax_obligation] id={row.id} → {row.tax_type} | amount = 0 | période={row.period_start}")
        if ids:
            conn.execute(text(f"DELETE FROM tax_obligation WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["tax_obligation"] = len(ids)
        print(f"✅ [tax_obligation] {len(ids)} ligne(s) supprimée(s)\n")

        # 4. training — cost_tnd = 0
        r = conn.execute(text("""
            SELECT id, training_type, training_date FROM training
            WHERE cost_tnd = 0
        """))
        rows = r.fetchall()
        ids = [row.id for row in rows]
        for row in rows:
            print(f"🗑️  [training] id={row.id} → {row.training_type} | cost = 0 | date={row.training_date}")
        if ids:
            conn.execute(text(f"DELETE FROM training WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["training"] = len(ids)
        print(f"✅ [training] {len(ids)} ligne(s) supprimée(s)\n")

        # 5. waste_management — weight_kg > 500
        r = conn.execute(text("""
            SELECT id, site, waste_type, weight_kg, period_date FROM waste_management
            WHERE weight_kg > 500
        """))
        rows = r.fetchall()
        ids = [row.id for row in rows]
        for row in rows:
            print(f"🗑️  [waste_management] id={row.id} → {row.site} | {row.waste_type} | {row.weight_kg}kg | {row.period_date}")
        if ids:
            conn.execute(text(f"DELETE FROM waste_management WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["waste_management"] = len(ids)
        print(f"✅ [waste_management] {len(ids)} ligne(s) supprimée(s)\n")

        # 6. co2_emission — co2_kg > 800000
        r = conn.execute(text("""
            SELECT id, route, co2_kg, period_date FROM co2_emission
            WHERE co2_kg > 800000
        """))
        rows = r.fetchall()
        ids = [row.id for row in rows]
        for row in rows:
            print(f"🗑️  [co2_emission] id={row.id} → {row.route} | co2={row.co2_kg} | {row.period_date}")
        if ids:
            conn.execute(text(f"DELETE FROM co2_emission WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["co2_emission"] = len(ids)
        print(f"✅ [co2_emission] {len(ids)} ligne(s) supprimée(s)\n")

        # 7. fuel_surcharge — amount_tnd > 60000
        r = conn.execute(text("""
            SELECT id, route, amount_tnd, period_date FROM fuel_surcharge
            WHERE amount_tnd > 60000
        """))
        rows = r.fetchall()
        ids = [row.id for row in rows]
        for row in rows:
            print(f"🗑️  [fuel_surcharge] id={row.id} → {row.route} | amount={row.amount_tnd} | {row.period_date}")
        if ids:
            conn.execute(text(f"DELETE FROM fuel_surcharge WHERE id IN ({','.join(map(str,ids))})"))
            conn.commit()
        rapport["fuel_surcharge"] = len(ids)
        print(f"✅ [fuel_surcharge] {len(ids)} ligne(s) supprimée(s)\n")

    total = sum(rapport.values())
    print(f"🎉 ETL terminé avec succès — {total} ligne(s) sale(s) supprimée(s) au total\n")
    return rapport


if __name__ == "__main__":
    run_etl()