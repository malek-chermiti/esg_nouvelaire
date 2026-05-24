import json
import os
import logging
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.models import Anomaly, Kpi, Recommendation


load_dotenv()
logger = logging.getLogger(__name__)


class AIService:
    """Service for generating AI recommendations from anomalies."""

    client = OpenAI(
        api_key=os.getenv("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )

    @staticmethod
    def _priority_from_severity(severity: Optional[str]) -> str:
        severity_value = (severity or "").strip().lower()
        if severity_value == "critique":
            return "HIGH"
        if severity_value == "haute":
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _format_number(value) -> str:
        try:
            return f"{float(value):.3f}"
        except (TypeError, ValueError):
            return "0.000"

    @staticmethod
    def _kpi_context(kpi_code: str) -> str:
        code = (kpi_code or "").strip().upper()

        contexts = {
            "CO2": "Concentre-toi sur la reduction des emissions, l'optimisation des vols et la consommation carburant.",
            "FUEL_SURCHARGE": "Concentre-toi sur la maitrise des couts carburant, la facturation et les ecarts de surcharge.",
            "WASTE": "Concentre-toi sur le tri a la source, le recyclage, la reduction des dechets et les filieres de traitement.",
            "PARITE_HF": "Concentre-toi sur le recrutement, la promotion interne, l'egalite des opportunites et le suivi des ecarts H/F.",
            "FORMATION": "Concentre-toi sur le plan de formation, la couverture des equipes et le nombre d'heures de formation.",
            "LTIR": "Concentre-toi sur la prevention des accidents, les EPI, la formation securite et l'analyse des causes racines.",
            "PAYMENT_TRACE": "Concentre-toi sur la traçabilite des paiements, le controle des circuits d'approbation et la documentation.",
            "TAX_OBLIGAT": "Concentre-toi sur la conformite fiscale, les echeances et la mise a jour des statuts de paiement.",
            "AVIA_ACTIVE": "Concentre-toi sur la validite des licences, le suivi des dates d'expiration et les renouvellements.",
        }

        return contexts.get(code, "Concentre-toi sur des actions correctives concretes, mesurables et adaptees au KPI.")

    @staticmethod
    def _build_structured_payload(
        *,
        kpi_code: str,
        anomaly: Anomaly,
        analysis: str,
        recommendation: str,
        priority: str,
        impact_estimated: str,
        title: str,
        anomaly_description: str,
    ) -> str:
        payload = {
            "title": title,
            "analysis": analysis,
            "recommendation": recommendation,
            "priority": priority,
            "impact_estimated": impact_estimated,
            "kpi_code": kpi_code,
            "anomaly_description": anomaly_description,
            "anomaly_id": anomaly.id,
            "detected_value": AIService._format_number(anomaly.detected_value),
            "expected_value": AIService._format_number(anomaly.expected_value),
        }
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def generate_recommendation(cls, db: Session, anomaly: Anomaly) -> Optional[Recommendation]:
        """
        Generate an ESG recommendation from an anomaly and persist it.

        Returns the created recommendation, or None if generation fails.
        """
        kpi_code = None
        if getattr(anomaly, "kpi", None) is not None:
            kpi_code = anomaly.kpi.code
        else:
            kpi = db.query(Kpi).filter(Kpi.id == anomaly.kpi_id).first()
            kpi_code = kpi.code if kpi else str(anomaly.kpi_id)

        severity_priority = cls._priority_from_severity(anomaly.severity)
        kpi_context = cls._kpi_context(kpi_code)
        anomaly_description = (anomaly.description or "").strip()

        prompt = (
            "Tu es un expert ESG pour Nouvelair. Analyse l'anomalie suivante et fournis "
            "une recommandation exploitable. Reponds exclusivement en JSON valide avec les "
            "champs title, analysis, recommendation, priority, impact_estimated.\n"
            "- analysis: diagnostic detaille du probleme, cause probable, impact metier et ESG.\n"
            "- recommendation: actions concretes et priorisees pour corriger le probleme. Ne recopie pas la description de l'anomalie; propose une action corrective differente et specifique au KPI. Utilise 3 decimales pour toutes les valeurs numeriques.\n"
            "Ecris plusieurs phrases si necessaire et sois plus detaille qu'un simple resume.\n\n"
            f"KPI code: {kpi_code}\n"
            f"KPI focus: {kpi_context}\n"
            f"Detected value: {cls._format_number(anomaly.detected_value)}\n"
            f"Target value: {cls._format_number(anomaly.expected_value)}\n"
            f"Anomaly description: {anomaly_description}\n"
            f"Severity: {anomaly.severity}\n"
            "Priority must follow severity mapping: critique=HIGH, haute=MEDIUM, moyenne=LOW."
        )

        try:
            logger.info(f"Generating recommendation for anomaly {anomaly.id} (KPI: {kpi_code})")
            response = cls.client.chat.completions.create(
                model=os.getenv("XAI_MODEL", "grok-beta"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an ESG analyst. Return only a strict JSON object with keys: "
                            "title, analysis, recommendation, priority, impact_estimated."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content or "{}"
            ai_data = json.loads(content)
            analysis = (ai_data.get("analysis") or "Aucune analyse detaillee fournie.").strip()
            recommendation = (ai_data.get("recommendation") or "Aucune recommandation detaillee fournie.").strip()
            title = ai_data.get("title") or "Recommandation ESG automatique"
            impact_estimated = ai_data.get("impact_estimated") or "Impact a evaluer"

            new_recommendation = Recommendation(
                anomaly_id=anomaly.id,
                title=title,
                description=cls._build_structured_payload(
                    kpi_code=kpi_code,
                    anomaly=anomaly,
                    analysis=analysis,
                    recommendation=recommendation,
                    priority=severity_priority,
                    impact_estimated=impact_estimated,
                    title=title,
                    anomaly_description=anomaly_description,
                ),
                priority=severity_priority,
                impact_estimated=impact_estimated,
                status="PENDING",
            )

            db.add(new_recommendation)
            db.commit()
            db.refresh(new_recommendation)
            logger.info(f"✓ Recommendation created (ID: {new_recommendation.id}) for anomaly {anomaly.id}")
            return new_recommendation

        except Exception as e:
            logger.error(f"AIService.generate_recommendation failed: {type(e).__name__}: {str(e)}")
            logger.info("Creating fallback recommendation without AI")
            
            # Create a fallback recommendation without AI
            try:
                severity_priority = cls._priority_from_severity(anomaly.severity)
                kpi_context = cls._kpi_context(kpi_code)
                anomaly_description = (anomaly.description or "").strip()
                analysis = (
                    f"Anomalie detectee pour le KPI {kpi_code}. "
                    f"Valeur actuelle {cls._format_number(anomaly.detected_value)} contre cible {cls._format_number(anomaly.expected_value)}. "
                    f"{anomaly_description}"
                )
                recommendation = f"{kpi_context} Adapter le plan d'action a l'anomalie: {anomaly_description}. Mettre en place un suivi des corrections sur les prochains cycles de mesure."
                new_recommendation = Recommendation(
                    anomaly_id=anomaly.id,
                    title=f"Recommandation ESG - {kpi_code}",
                    description=cls._build_structured_payload(
                        kpi_code=kpi_code,
                        anomaly=anomaly,
                        analysis=analysis,
                        recommendation=recommendation,
                        priority=severity_priority,
                        impact_estimated="À évaluer",
                        title=f"Recommandation ESG - {kpi_code}",
                        anomaly_description=anomaly_description,
                    ),
                    priority=severity_priority,
                    impact_estimated="À évaluer",
                    status="PENDING",
                )
                db.add(new_recommendation)
                db.commit()
                db.refresh(new_recommendation)
                logger.info(f"✓ Fallback recommendation created (ID: {new_recommendation.id}) for anomaly {anomaly.id}")
                return new_recommendation
            except Exception as fallback_error:
                logger.error(f"Fallback recommendation also failed: {type(fallback_error).__name__}: {str(fallback_error)}")
                db.rollback()
                return None
