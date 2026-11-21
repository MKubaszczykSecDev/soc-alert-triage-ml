## ML-Driven SOC Alert Triage Pipeline

An automated SOC alert triage and behavioral enrichment pipeline built to work alongside Wazuh SIEM. The system takes in raw JSON data from Wazuh, enriches authentication events with offline MaxMind GeoLite2 lookups and impossible travel velocity calculations, and transforms logs into normalized numerical feature vectors for a random forest classifier, the main purpose is separating routine background noise from high risk incidents to reduce analyst alert fatigue.

Full architectural designs, mathematical proofs, feature engineering rationale, and ongoing troubleshooting logs are documented in **Documents/Wazuh_Engineering_Specification.docx.**

## Architectural Pipeline Diagram

<img width="1643" height="631" alt="Screenshot 2026-11-17 223659" src="https://github.com/user-attachments/assets/03d4f908-c690-47f2-921a-6117c8c16558" />

## Project Status

* Milestone 1: Home lab & Wazuh SIEM configuration (COMPLETED)
* Milestone 2: System architecture, mathematics, and ML feature specification (COMPLETED)
* Milestone 3: Behavioral enrichment engine (src/enrichment.py - GeoLite2 & Haversine cache) (PENDING)
* Milestone 4: Feature preprocessing & random forest training pipeline (UPCOMING)
* Milestone 5: Live alert triage & evaluation (UPCOMING)
