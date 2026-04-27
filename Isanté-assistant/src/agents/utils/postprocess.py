# src/agents/utils/postprocess.py
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import re

# ---- Small helpers ----------------------------------------------------------

def _to_date(x: Any) -> Optional[date]:
    if x is None:
        return None
    if isinstance(x, date):
        return x
    if isinstance(x, datetime):
        return x.date()
    s = str(x).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt).date()
        except Exception:
            continue
    return None

def _days_between(a: Any, b: Any) -> Optional[int]:
    da, db = _to_date(a), _to_date(b)
    if da and db:
        return (db - da).days
    return None

def _pct(n: Optional[float]) -> Optional[float]:
    return round(n * 100.0, 2) if n is not None else None

def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None

def _extract_percent_from_question(q: str) -> Optional[float]:
    # e.g. "25%" -> 25.0
    m = re.search(r"(\d{1,3})\s*%", q or "", re.IGNORECASE)
    if m:
        try:
            v = float(m.group(1))
            if 0 <= v <= 100:
                return v
        except Exception:
            pass
    return None

# ---- Core analyzers ---------------------------------------------------------

def analyze_delay(rows: List[Dict[str, Any]], today: Optional[date] = None) -> List[str]:
    """
    Look for reimbursement delays using date_demande vs date_decision if available.
    Falls back to comparing date_decision to today when only one date is present.
    """
    insights = []
    today = today or date.today()

    for i, r in enumerate(rows, start=1):
        date_demande = r.get("date_demande") or r.get("date_creation")  # optional future column
        date_decision = r.get("date_decision")
        dlt = None

        if date_demande and date_decision:
            dlt = _days_between(date_demande, date_decision)
        elif date_demande and not date_decision:
            dlt = _days_between(date_demande, today)
        # else: not enough signal

        if dlt is not None:
            msg = f"Dossier {i}: délai constaté {dlt} jours"
            if dlt > 15:
                msg += " (au-delà du délai indicatif de 15 jours)."
            else:
                msg += " (dans le délai indicatif de 15 jours)."
            insights.append(msg)

    return insights

def analyze_amounts(rows: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Any]]:
    """
    Reconcile totals: total_ordonnance vs total_rembourse vs reste_a_payer.
    Also compute an implied ticket modérateur when possible.
    """
    insights = []
    facts: Dict[str, Any] = {}

    for i, r in enumerate(rows, start=1):
        tot_ord = _safe_float(r.get("total_ordonnance"))
        tot_remb = _safe_float(r.get("total_rembourse"))
        reste = _safe_float(r.get("reste_a_payer"))
        implied_tm = None

        # Basic reconciliation
        if tot_ord is not None and tot_remb is not None:
            expected_reste = round(tot_ord - tot_remb, 2)
            facts[f"dossier_{i}_expected_reste"] = expected_reste
            if reste is not None:
                delta = round(reste - expected_reste, 2)
                if abs(delta) <= 0.01:
                    insights.append(f"Dossier {i}: reste à payer cohérent ({reste} ≈ {expected_reste}).")
                else:
                    insights.append(f"Dossier {i}: écart sur le reste à payer ({reste} vs attendu {expected_reste}, Δ={delta}).")

        # Implied ticket modérateur
        if tot_ord and reste is not None and tot_ord > 0:
            implied_tm = _pct(reste / tot_ord)
            if implied_tm is not None:
                insights.append(f"Dossier {i}: ticket modérateur implicite ≈ {implied_tm} %.")
                facts[f"dossier_{i}_ticket_mod_implicite_pct"] = implied_tm

        # Anomaly detection
        if tot_ord is not None and reste is not None and tot_ord >= 0:
            if reste < 0:
                insights.append(f"Dossier {i}: anomalie — reste à payer négatif ({reste}).")
            if reste > (tot_ord * 0.3):
                insights.append(f"Dossier {i}: alerte — reste à payer élevé (>30 % de l'ordonnance).")

    return insights, facts

def analyze_ticket_from_question(question: str, rows: List[Dict[str, Any]]) -> List[str]:
    """
    Check if the ticket modérateur mentioned in the question matches the implied one.
    """
    target_pct = _extract_percent_from_question(question or "")
    if target_pct is None:
        return []

    msgs: List[str] = []
    for i, r in enumerate(rows, start=1):
        tot_ord = _safe_float(r.get("total_ordonnance"))
        reste = _safe_float(r.get("reste_a_payer"))

        if tot_ord and reste is not None and tot_ord > 0:
            implied = (reste / tot_ord) * 100.0
            diff = round(implied - target_pct, 2)

            if abs(diff) <= 1.0:
                msgs.append(f"Dossier {i}: le ticket appliqué (~{round(implied,2)} %) correspond à ~{target_pct} %.")
            else:
                direction = "au-dessus" if diff > 0 else "au-dessous"
                msgs.append(f"Dossier {i}: ticket implicite ~{round(implied,2)} % ({direction} de {abs(diff)} pp vs {target_pct} %).")

    return msgs

def analyze_rows(question: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point: analyze rows and return insights, facts, and summary.
    """
    insights: List[str] = []
    facts: Dict[str, Any] = {}

    # Run all analyzers
    delay_insights = analyze_delay(rows)
    if delay_insights:
        insights.extend(delay_insights)

    amt_insights, amt_facts = analyze_amounts(rows)
    if amt_insights:
        insights.extend(amt_insights)
    facts.update(amt_facts)

    ticket_msgs = analyze_ticket_from_question(question, rows)
    if ticket_msgs:
        insights.extend(ticket_msgs)

    # Generate summary
    if insights:
        summary = " | ".join(insights[:4])  # Limit to first 4 insights
    else:
        summary = "Aucune incohérence évidente détectée sur les dates et montants disponibles."

    return {
        "insights": insights,
        "facts": facts,
        "summary": summary
    }