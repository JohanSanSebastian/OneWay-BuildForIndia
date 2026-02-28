# Product Requirements Document (PRD): Disaster & Infrastructure Sentinel

## 1. Product Vision

To provide the citizens of Kerala with a seamless, "zero-friction" interface for reporting localized disasters and infrastructure failures, using AI to bridge the gap between a captured image and an actionable government response.

## 2. Core User Flow

1. **Capture:** User takes a photo of an issue (e.g., a fallen tree on MC Road, waterlogging in Panampilly Nagar).
2. **Analyze:** The AI Agent (Claude/Gemini) identifies the issue, severity, and precise GPS coordinates.
3. **Map:** The incident is live-plotted on a Kerala-specific geospatial dashboard.
4. **Action:** The system identifies the relevant local authority (KSEB, PWD, Fire & Rescue) and initiates contact.

---

## 3. Functional Requirements

### 3.1 AI Vision & Classification

* **Scene Understanding:** Must distinguish between categories: *Natural Disaster* (landslide, flood), *Infrastructure* (broken power line, pothole), and *Obstruction* (fallen tree, vehicle accident).
* **Severity Scoring:** AI must assign a priority level (P1 to P4) to dictate the urgency of the automated call.
* **OCR Integration:** Extract text from nearby landmarks or signboards to verify location if GPS metadata is weak.

### 3.2 Geospatial Mapping (Kerala Focus)

* **Map Interface:** Use a minimalist Kerala map overlay (as discussed for your updates.md).
* **Data Constancy:** Graphs and maps must only show *actual* reported data. **No sample markers.**
* **KSMART Integration:** Sync with KSMART (Kerala Solutions for Managing Administrative Reformation and Transformation) to verify ward-level boundaries for reporting.

### 3.3 The "Agentic" Action Layer

* **Authority Identification:** Based on location and issue type, the backend must query a directory to find:
* The specific **LSGD** (Local Self Government Department) contact.
* The nearest **KSEB** section office (for electrical issues).
* The nearest **Police/Fire station**.


* **Communication Bridge:** * **Automated Briefing:** Generate a concise script for the human user to read.
* **AI Assist:** If the user is stressed, the AI can initiate a VoIP call to the helpline, play a synthesized summary of the issue, and then patch the human in.



---

## 4. Technical Constraints (Architecture)

| Component | Specification |
| --- | --- |
| **Frontend** | Minimalist/Modern. **No processing logic**; strictly UI rendering. |
| **Backend** | All image processing, API calls to KSMART/Maps, and LLM orchestration. |
| **Typography** | Inter / Modern Minimalist (as per branding update). |
| **State** | User's map view and reported "Active Issues" must persist through refreshes. |
| **Assets** | Payment/Donation QR (if applicable) must use `api-qr.png`. |

---

## 5. Privacy & Ethics

* **Anonymization:** Automatically blur faces or license plates in the "Public Map" view.
* **Verification:** Use the agent to bypass CAPTCHAs (utilizing your existing **KSMART approval**) to log formal complaints in government portals autonomously.

---

## 6. Success Metrics

* **Time to Map:** Seconds from "Photo Upload" to "Marker Appearing on Map."
* **Resolution Loop:** Number of reports that successfully transitioned from "Reported" to "Authority Notified."