from typing import Dict, Any, List

class RRHHAgent:
    """Placeholder de RRHH: genera JD simples y matrices de competencias."""
    def build_job_profile(self, rol: str) -> Dict[str, Any]:
        return {
            "rol": rol,
            "responsabilidades": ["Reclutamiento", "Onboarding", "Capacitación"],
            "kpis": ["time_to_hire", "retention_90d"]
        }
