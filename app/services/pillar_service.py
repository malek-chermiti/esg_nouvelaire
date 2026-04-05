from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.models.models import (
    Co2Emission, WasteManagement, FuelSurcharge,
    Employee, Training, WorkAccident,
    PaymentTracking, TaxObligation, AviationLicense,
    Kpi, Pillar
)
from app.schemas.pillar_schemas import PillarScoreResponse, KpiScoreDetail, GlobalScoreResponse, EvolutionScoreResponse


class PillarService:
    
    @staticmethod
    def calculate_kpi_score(realized: float, target: float) -> float:
        """Calculate KPI score with target cap and rounding"""
        if target == 0 or target is None:
            return 0.0
        score = (realized / target) * 100
        score = min(score, 100)  # Cap at 100
        return round(max(score, 0), 2)  # Min 0, rounded to 2 decimals
    
    @staticmethod
    def get_kpi_realized_value(db: Session, kpi_code: str, year: int = None) -> float:
        """Get realized value for a specific KPI"""
        current_year = year
        
        # Environnement KPIs
        if kpi_code == "co2":
            query = db.query(func.sum(Co2Emission.co2_kg)).filter(Co2Emission.co2_kg.isnot(None))
            if year:
                query = query.filter(extract('year', Co2Emission.period_date) == year)
            result = query.scalar()
            return float(result) if result else 0.0
        
        elif kpi_code == "fuel_surcharge":
            query = db.query(func.sum(FuelSurcharge.amount_tnd)).filter(FuelSurcharge.amount_tnd.isnot(None))
            if year:
                query = query.filter(extract('year', FuelSurcharge.period_date) == year)
            result = query.scalar()
            return float(result) if result else 0.0
        
        # Social KPIs
        elif kpi_code == "WASTE":
            if year:
                total = db.query(func.count(Employee.id)).filter(
                    extract('year', Employee.hire_date) <= year
                ).scalar()
                active = db.query(func.count(Employee.id)).filter(
                    Employee.is_active == 1,
                    extract('year', Employee.hire_date) <= year
                ).scalar()
            else:
                total = db.query(func.count(Employee.id)).scalar()
                active = db.query(func.count(Employee.id)).filter(Employee.is_active == 1).scalar()
            if total == 0:
                return 0.0
            return round((active / total) * 100, 2)
        
        elif kpi_code == "LTIR":
            query = db.query(func.count(WorkAccident.id))
            if year:
                query = query.filter(extract('year', WorkAccident.accident_date) == year)
            result = query.scalar()
            return float(result) if result else 0.0
        
        elif kpi_code == "PARITE_HF":
            query = db.query(func.sum(Training.hours)).filter(Training.hours.isnot(None))
            if year:
                query = query.filter(extract('year', Training.training_date) == year)
            result = query.scalar()
            return float(result) if result else 0.0
        
        # Gouvernance KPIs
        elif kpi_code == "PAYMENT_TRACE":
            if year:
                total = db.query(func.count(PaymentTracking.id)).filter(
                    extract('year', PaymentTracking.payment_date) == year
                ).scalar()
                traceable = db.query(func.count(PaymentTracking.id)).filter(
                    PaymentTracking.is_traceable == 1,
                    extract('year', PaymentTracking.payment_date) == year
                ).scalar()
            else:
                total = db.query(func.count(PaymentTracking.id)).scalar()
                traceable = db.query(func.count(PaymentTracking.id)).filter(
                    PaymentTracking.is_traceable == 1
                ).scalar()
            if total == 0:
                return 0.0
            return round((traceable / total) * 100, 2)
        
        elif kpi_code == "TAX_OBLIGAT":
            if year:
                total = db.query(func.count(TaxObligation.id)).filter(
                    extract('year', TaxObligation.period_start) == year
                ).scalar()
                paid = db.query(func.count(TaxObligation.id)).filter(
                    TaxObligation.status == 'PAID',
                    extract('year', TaxObligation.period_start) == year
                ).scalar()
            else:
                total = db.query(func.count(TaxObligation.id)).scalar()
                paid = db.query(func.count(TaxObligation.id)).filter(
                    TaxObligation.status == 'PAID'
                ).scalar()
            if total == 0:
                return 0.0
            return round((paid / total) * 100, 2)
        
        elif kpi_code == "AVIA_ACTIVE":
            if year:
                total = db.query(func.count(AviationLicense.id)).filter(
                    extract('year', AviationLicense.period_date) == year
                ).scalar()
                active = db.query(func.count(AviationLicense.id)).filter(
                    AviationLicense.status == 'ACTIVE',
                    extract('year', AviationLicense.period_date) == year
                ).scalar()
            else:
                total = db.query(func.count(AviationLicense.id)).scalar()
                active = db.query(func.count(AviationLicense.id)).filter(
                    AviationLicense.status == 'ACTIVE'
                ).scalar()
            if total == 0:
                return 0.0
            return round((active / total) * 100, 2)
        
        return 0.0
    
    @staticmethod
    def get_pillar_score(db: Session, pillar_code: str, year: int = None) -> PillarScoreResponse:
        """Calculate score for a specific pillar"""
        # Fetch pillar
        pillar = db.query(Pillar).filter(Pillar.code == pillar_code).first()
        if not pillar:
            raise ValueError(f"Pillar with code {pillar_code} not found")
        
        # Fetch KPIs for this pillar
        kpis = db.query(Kpi).filter(Kpi.pillar_id == pillar.id).all()
        if not kpis:
            raise ValueError(f"No KPIs found for pillar {pillar_code}")
        
        # Calculate KPI scores
        kpi_scores = []
        total_pillar_score = 0.0
        
        for kpi in kpis:
            # Get realized value
            realized = PillarService.get_kpi_realized_value(db, kpi.code, year)
            
            # Calculate KPI score
            target = float(kpi.target) if kpi.target else 0
            score_kpi = PillarService.calculate_kpi_score(realized, target)
            
            # Add to pillar score with weight
            weight = float(kpi.weight) if kpi.weight else 0
            total_pillar_score += score_kpi * weight
            
            # Store KPI detail
            kpi_scores.append(KpiScoreDetail(
                code=kpi.code,
                realized=round(realized, 2),
                target=round(target, 2),
                score_kpi=score_kpi,
                weight=round(weight, 2)
            ))
        
        # Determine pillar name from code
        pillar_names = {
            'E': 'Environnement',
            'S': 'Social',
            'G': 'Gouvernance'
        }
        pillar_name = pillar_names.get(pillar_code, pillar.name)
        
        return PillarScoreResponse(
            pillar=pillar_name,
            score=round(total_pillar_score, 2),
            weight=round(float(pillar.weight), 2),
            kpis=kpi_scores
        )
    
    @staticmethod
    def get_global_score(db: Session, year: int = None) -> GlobalScoreResponse:
        """Calculate global score across all pillars"""
        # Fetch all pillars
        pillars = db.query(Pillar).all()
        if not pillars:
            raise ValueError("No pillars found in database")
        
        details = {}
        total_global_score = 0.0
        
        for pillar in pillars:
            # Calculate pillar score
            pillar_score_response = PillarService.get_pillar_score(db, pillar.code, year)
            
            pillar_name = pillar_score_response.pillar.lower()
            details[pillar_name] = {
                "score": pillar_score_response.score,
                "weight": pillar_score_response.weight
            }
            
            # Add to global score with pillar weight
            pillar_weight = float(pillar.weight) if pillar.weight else 0
            total_global_score += pillar_score_response.score * pillar_weight
        
        return GlobalScoreResponse(
            score_global=round(total_global_score, 2),
            details=details
        )
    
    @staticmethod
    def get_kpi_realized_value_by_month(db: Session, kpi_code: str, year: int, month: int) -> float:
        """Get realized value for a specific KPI for a specific month"""
        
        # Environnement KPIs
        if kpi_code == "co2":
            query = db.query(func.sum(Co2Emission.co2_kg)).filter(
                Co2Emission.co2_kg.isnot(None),
                extract('year', Co2Emission.period_date) == year,
                extract('month', Co2Emission.period_date) == month
            )
            result = query.scalar()
            return float(result) if result else 0.0
        
        elif kpi_code == "fuel_surcharge":
            query = db.query(func.sum(FuelSurcharge.amount_tnd)).filter(
                FuelSurcharge.amount_tnd.isnot(None),
                extract('year', FuelSurcharge.period_date) == year,
                extract('month', FuelSurcharge.period_date) == month
            )
            result = query.scalar()
            return float(result) if result else 0.0
        
        # Social KPIs
        elif kpi_code == "WASTE":
            total = db.query(func.count(Employee.id)).filter(
                extract('year', Employee.hire_date) <= year,
                Employee.is_active.isnot(None)
            ).scalar()
            active = db.query(func.count(Employee.id)).filter(
                Employee.is_active == 1,
                extract('year', Employee.hire_date) <= year
            ).scalar()
            if total == 0:
                return 0.0
            return round((active / total) * 100, 2)
        
        elif kpi_code == "LTIR":
            query = db.query(func.count(WorkAccident.id)).filter(
                extract('year', WorkAccident.accident_date) == year,
                extract('month', WorkAccident.accident_date) == month
            )
            result = query.scalar()
            return float(result) if result else 0.0
        
        elif kpi_code == "PARITE_HF":
            query = db.query(func.sum(Training.hours)).filter(
                Training.hours.isnot(None),
                extract('year', Training.training_date) == year,
                extract('month', Training.training_date) == month
            )
            result = query.scalar()
            return float(result) if result else 0.0
        
        # Gouvernance KPIs
        elif kpi_code == "PAYMENT_TRACE":
            total = db.query(func.count(PaymentTracking.id)).filter(
                extract('year', PaymentTracking.payment_date) == year,
                extract('month', PaymentTracking.payment_date) == month
            ).scalar()
            traceable = db.query(func.count(PaymentTracking.id)).filter(
                PaymentTracking.is_traceable == 1,
                extract('year', PaymentTracking.payment_date) == year,
                extract('month', PaymentTracking.payment_date) == month
            ).scalar()
            if total == 0:
                return 0.0
            return round((traceable / total) * 100, 2)
        
        elif kpi_code == "TAX_OBLIGAT":
            total = db.query(func.count(TaxObligation.id)).filter(
                extract('year', TaxObligation.period_start) == year,
                extract('month', TaxObligation.period_start) == month
            ).scalar()
            paid = db.query(func.count(TaxObligation.id)).filter(
                TaxObligation.status == 'PAID',
                extract('year', TaxObligation.period_start) == year,
                extract('month', TaxObligation.period_start) == month
            ).scalar()
            if total == 0:
                return 0.0
            return round((paid / total) * 100, 2)
        
        elif kpi_code == "AVIA_ACTIVE":
            total = db.query(func.count(AviationLicense.id)).filter(
                extract('year', AviationLicense.period_date) == year,
                extract('month', AviationLicense.period_date) == month
            ).scalar()
            active = db.query(func.count(AviationLicense.id)).filter(
                AviationLicense.status == 'ACTIVE',
                extract('year', AviationLicense.period_date) == year,
                extract('month', AviationLicense.period_date) == month
            ).scalar()
            if total == 0:
                return 0.0
            return round((active / total) * 100, 2)
        
        return 0.0
    
    @staticmethod
    def get_monthly_scores(db: Session, year: int = None) -> EvolutionScoreResponse:
        """Calculate monthly ESG scores evolution for 12 months"""
        if year is None:
            year = datetime.now().year - 1
        
        # Month labels in French
        month_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
        
        # Initialize series
        series = {
            "global": [],
            "E": [],
            "S": [],
            "G": []
        }
        
        # Fetch all pillars and KPIs
        pillars = db.query(Pillar).all()
        pillar_dict = {p.code: p for p in pillars}
        kpis = db.query(Kpi).all()
        kpi_dict = {k.code: k for k in kpis}
        
        # Calculate scores for each month
        for month in range(1, 13):
            pillar_scores = {}
            
            # Calculate each pillar score
            for pillar in pillars:
                total_score = 0.0
                pillar_kpis = [k for k in kpis if k.pillar_id == pillar.id]
                
                for kpi in pillar_kpis:
                    # Get realized value for this month
                    realized = PillarService.get_kpi_realized_value_by_month(db, kpi.code, year, month)
                    
                    # Calculate KPI score
                    target = float(kpi.target) if kpi.target else 0
                    score_kpi = PillarService.calculate_kpi_score(realized, target)
                    
                    # Add to pillar score with weight
                    weight = float(kpi.weight) if kpi.weight else 0
                    total_score += score_kpi * weight
                
                pillar_scores[pillar.code] = round(total_score, 2)
            
            # Add pillar scores to series
            series["E"].append(pillar_scores.get('E', 0))
            series["S"].append(pillar_scores.get('S', 0))
            series["G"].append(pillar_scores.get('G', 0))
            
            # Calculate global score
            global_score = 0.0
            for pillar in pillars:
                pillar_weight = float(pillar.weight) if pillar.weight else 0
                global_score += pillar_scores.get(pillar.code, 0) * pillar_weight
            
            series["global"].append(round(global_score, 2))
        
        return EvolutionScoreResponse(
            labels=month_labels,
            series=series
        )
