from app.models.models import Anomaly, Kpi, Co2Emission, FuelSurcharge, WasteManagement, Employee, Training, WorkAccident, PaymentTracking, TaxObligation, AviationLicense
from app.database import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import func
import decimal
from app.services import (
    co2_service, fuel_surcharge_service, waste_management_service,
    employee_service, training_service, work_accident_service,
    payment_tracking_service, tax_obligation_service, aviation_license_service
) 


class AnomalyDetectionService:
    
    @staticmethod
    def detect_anomalies():
        """Detect anomalies dynamically from KPI table"""
        db: Session = SessionLocal()
        detected = []
        
        try:
            kpis = db.query(Kpi).all()
            
            for kpi in kpis:
                try:
                    real_value = AnomalyDetectionService.get_kpi_real_value(db, kpi.code)
                    
                    if real_value is None:
                        continue
                    
                    direction = (kpi.better_direction or "").strip().upper()
                    if not direction:
                        continue
                    
                    gap = AnomalyDetectionService.calc_gap(
                        real_value,
                        float(kpi.target),
                        direction
                    )
                    
                    if gap > 0:
                        severity = AnomalyDetectionService.calc_severity(gap)
                        z_score = AnomalyDetectionService.calc_z_score(gap)
                        
                        anomaly = Anomaly(
                            kpi_id=kpi.id,
                            detected_value=decimal.Decimal(str(real_value)),
                            expected_value=decimal.Decimal(str(kpi.target)),
                            z_score=decimal.Decimal(str(z_score)),
                            severity=severity,
                            status="NEW",
                            date_detected=datetime.utcnow(),
                            description=f"{kpi.name}: {gap:.2f}% gap"
                        )
                        db.add(anomaly)
                        db.commit()
                        db.refresh(anomaly)
                        detected.append(anomaly)
                
                except Exception as e:
                    print(f"Error processing KPI {kpi.code}: {str(e)}")
                    continue
        
        finally:
            db.close()
        
        return detected

    @staticmethod
    def get_kpi_real_value(db: Session, kpi_code: str):
        """Get real value of KPI from corresponding service"""
        
        try:
            if kpi_code == "co2":
                result = co2_service.get_monthly_co2_score()
                if result and "monthly_scores" in result and result["monthly_scores"]:
                    return float(result["monthly_scores"][-1]["total_co2_kg"])
            
            elif kpi_code == "fuel_surcharge":
                result = fuel_surcharge_service.get_monthly_fuel_surcharge_score()
                if result and "monthly_scores" in result and result["monthly_scores"]:
                    return float(result["monthly_scores"][-1]["total_amount_tnd"])
            
            elif kpi_code == "WASTE":
                result = waste_management_service.get_recycling_rate()
                if result and "monthly_scores" in result and result["monthly_scores"]:
                    return float(result["monthly_scores"][-1]["total_weight_kg"])
            
            elif kpi_code == "PARITE_HF":
                result = employee_service.get_gender_stats()
                if result:
                    return float(result.get("global_female_percentage", 0))
            
            elif kpi_code == "FORMATION":
                result = training_service.get_training_hours_per_quarter(2025)
                if result:
                    return float(result.get("total_hours_year", 0))
            
            elif kpi_code == "LTIR":
                result = work_accident_service.get_ltir_monthly()
                if result:
                    return float(result.get("average_ltir", 0))
            
            elif kpi_code == "PAYMENT_TRACE":
                result = payment_tracking_service.get_traceable_payments()
                if result:
                    return float(result.get("percentage", 0))
            
            elif kpi_code == "TAX_OBLIGAT":
                result = tax_obligation_service.get_tax_obligations()
                if result:
                    return float(result.get("percentage", 0))
            
            elif kpi_code == "AVIA_ACTIVE":
                result = aviation_license_service.get_aviation_licenses()
                if result:
                    return float(result.get("percentage", 0))
        
        except Exception as e:
            print(f"Error getting KPI value for {kpi_code}: {str(e)}")
        
        return None

    @staticmethod
    def detect_monthly_anomalies(kpi_code: str):
        """Scan monthly history and identify anomalies for each KPI code"""
        db: Session = SessionLocal()
        anomalies = []
        
        try:
            # Get KPI configuration from database
            kpi = db.query(Kpi).filter(Kpi.code == kpi_code).first()
            if not kpi:
                return []
            
            target_value = float(kpi.target)
            direction = (kpi.better_direction or "").strip().upper()
            
            if not direction:
                return []
            
            # Get monthly data from service
            data_source = None
            val_key = ""
            month_key = "month"
            
            try:
                if kpi_code == "co2":
                    data_source = co2_service.get_monthly_co2_score()
                    val_key = "total_co2_kg"
                
                elif kpi_code == "fuel_surcharge":
                    data_source = fuel_surcharge_service.get_monthly_fuel_surcharge_score()
                    val_key = "total_amount_tnd"
                
                elif kpi_code == "WASTE":
                    data_source = waste_management_service.get_recycling_rate()
                    val_key = "total_weight_kg"
                
                elif kpi_code == "PARITE_HF":
                    result = employee_service.get_gender_stats()
                    if result:
                        data_source = {"monthly_scores": [{"month": "Current", "val": result.get("global_female_percentage", 0)}]}
                        val_key = "val"
                
                elif kpi_code == "FORMATION":
                    result = training_service.get_training_hours_per_quarter(2025)
                    if result:
                        data_source = {"monthly_scores": [{"month": "Current", "val": result.get("total_hours_year", 0)}]}
                        val_key = "val"
                
                elif kpi_code == "LTIR":
                    result = work_accident_service.get_ltir_monthly()
                    if result:
                        data_source = {"monthly_scores": [{"month": "Current", "val": result.get("average_ltir", 0)}]}
                        val_key = "val"
                
                elif kpi_code == "PAYMENT_TRACE":
                    result = payment_tracking_service.get_traceable_payments()
                    if result:
                        data_source = {"monthly_scores": [{"month": "Current", "val": result.get("percentage", 0)}]}
                        val_key = "val"
                
                elif kpi_code == "TAX_OBLIGAT":
                    result = tax_obligation_service.get_tax_obligations()
                    if result:
                        data_source = {"monthly_scores": [{"month": "Current", "val": result.get("percentage", 0)}]}
                        val_key = "val"
                
                elif kpi_code == "AVIA_ACTIVE":
                    result = aviation_license_service.get_aviation_licenses()
                    if result:
                        data_source = {"monthly_scores": [{"month": "Current", "val": result.get("percentage", 0)}]}
                        val_key = "val"
            
            except Exception as e:
                print(f"Error fetching monthly data for {kpi_code}: {str(e)}")
                return []
            
            # Analyze monthly scores
            if data_source and "monthly_scores" in data_source:
                for entry in data_source["monthly_scores"]:
                    real_val = entry.get(val_key, 0)
                    month = entry.get(month_key, "Unknown")
                    
                    # Calculate gap and severity
                    gap = AnomalyDetectionService.calc_gap(real_val, target_value, direction)
                    severity = AnomalyDetectionService.calc_severity(gap)
                    
                    # Record as anomaly if gap exceeds threshold (> 5%)
                    if gap > 5:
                        anomalies.append({
                            "kpi_code": kpi_code,
                            "kpi_name": kpi.name,
                            "month": month,
                            "real_value": real_val,
                            "target": target_value,
                            "gap_percentage": round(gap, 2),
                            "severity": severity,
                            "direction": direction
                        })
        
        except Exception as e:
            print(f"Error detecting monthly anomalies for {kpi_code}: {str(e)}")
        
        finally:
            db.close()
        
        return anomalies

    @staticmethod
    def calc_gap(real_value, target_value, direction):
        """Calculate gap percentage based on KPI direction"""
        if target_value == 0 or real_value is None:
            return 0
        
        # Case where we need to stay BELOW a limit (ex: CO2, Accidents, Waste)
        if direction == "LOWER":
            if real_value > target_value:
                return ((real_value - target_value) / target_value) * 100
            return 0
        
        # Case where we need to be ABOVE a limit (ex: Parity, Training, Traceability)
        elif direction in ["HIGHER", "UP"]:
            if real_value < target_value:
                return ((target_value - real_value) / target_value) * 100
            return 0
        
        return 0

    @staticmethod
    def calc_severity(gap_percentage):
        """Determine severity level based on gap"""
        if gap_percentage > 20:
            return "critique"
        elif gap_percentage > 10:
            return "haute"
        elif gap_percentage > 5:
            return "moyenne"
        else:
            return "basse"

    @staticmethod
    def calc_z_score(gap_percentage):
        """Calculate z-score"""
        mean = 10
        std_dev = 5
        return (gap_percentage - mean) / std_dev if std_dev != 0 else 0

    @staticmethod
    def get_open_anomalies(db: Session):
        """Get open anomalies"""
        return db.query(Anomaly).filter(Anomaly.status != 'résolu').all()

    @staticmethod
    def get_critical_anomalies(db: Session):
        """Get critical anomalies"""
        return db.query(Anomaly).filter(Anomaly.severity.in_(['critique', 'haute'])).all()

    @staticmethod
    def mark_resolved(db: Session, anomaly_id: int):
        """Mark anomaly as resolved"""
        anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
        if anomaly:
            anomaly.status = 'résolu'
            db.commit()
            return anomaly
        return None

    @staticmethod
    def get_stats(db: Session):
        """Get anomaly statistics"""
        return {
            "total_open": db.query(Anomaly).filter(Anomaly.status != 'résolu').count(),
            "total_critical": db.query(Anomaly).filter(Anomaly.severity.in_(['critique', 'haute'])).count(),
            "by_severity": {
                sev: db.query(Anomaly).filter(Anomaly.severity == sev).count()
                for sev in ['critique', 'haute', 'moyenne', 'basse']
            }
        }

    @staticmethod
    def detect_all_monthly_anomalies():
        """Detect monthly anomalies for all KPI codes"""
        db: Session = SessionLocal()
        all_anomalies = []
        
        try:
            kpi_codes = [
                "co2", "fuel_surcharge", "WASTE", "PARITE_HF", 
                "FORMATION", "LTIR", "PAYMENT_TRACE", "TAX_OBLIGAT", "AVIA_ACTIVE"
            ]
            
            for kpi_code in kpi_codes:
                monthly_anomalies = AnomalyDetectionService.detect_monthly_anomalies(kpi_code)
                all_anomalies.extend(monthly_anomalies)
        
        finally:
            db.close()
        
        return all_anomalies
