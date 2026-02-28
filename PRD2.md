---

# PRD Addendum: OneWay Sentinel (Motor Violation Assistant)

## 1. Feature Overview

OneWay Sentinel allows users to report traffic violations and resolve parking disputes autonomously. It bridges the gap between seeing a violation and official reporting by automating evidence verification, data extraction, and communication.

## 2. Functional Requirements

### 2.1 Evidence Verification & Metadata Processing

* **Metadata Extraction:** The system must parse EXIF data from uploaded images to extract GPS coordinates ($Latitude, Longitude$) and the $Timestamp$ of the violation.
* **AI Content Verification:** Use Bedrock Vision to analyze the image for "AI-generated artifacts" or "Digital manipulation" to ensure the evidence is authentic before submission.
* **Geolocation Validation:** Cross-reference extracted GPS data with a reverse-geocoding API to provide a human-readable address (e.g., "Near NIT Calicut Main Gate").

### 2.2 Bedrock-Powered ANPR & Violation Reporting

* **Plate Recognition:** Use Amazon Bedrock to identify and transcribe the vehicle's license plate number from the image.
* **Contextual Description:** The AI analyzes the image (e.g., "Rider without a helmet," "Triple riding," "Parking in a No-Parking zone") to draft a formal description.
* **Automated MVD Emailer:** Automatically generate and send a formatted email to the Motor Vehicles Department (MVD) containing:
* The high-res image.
* Extracted plate number.
* Location and time.
* Detailed violation description.



### 2.3 Dispute Resolution (Parking Assistant)

* **Obstruction Reporting:** For scenarios where a vehicle is blocked, the user uploads a photo of the offending car.
* **Owner Identification:** The system queries the internal "OneWay Registry" to match the ANPR-detected plate with an owner's phone number.
* **Automated Warning (Dummy Voiceflow):** * Trigger a webhook to a voice service.
* **Current State:** Log the "Call Triggered" event in the dashboard with a status of `Pending Voice Integration`.



---

## 3. Technical Architecture for Coding Agents

### Implementation File: `sentinel_engine.py`

This logic should be provided to your AI agent to handle the Bedrock integration.

```python
import boto3
import json

# Bedrock ANPR & AI Verification Logic
def analyze_violation(image_bytes):
    bedrock = boto3.client(service_name='bedrock-runtime')
    
    prompt = """
    Analyze this image:
    1. Extract the vehicle license plate number (ANPR).
    2. Identify the traffic violation (e.g. no helmet, wrong side, obstruction).
    3. Verify if this image appears to be AI-generated or manipulated.
    Return as JSON: {plate: string, violation: string, is_authentic: boolean, confidence: float}
    """
    
    # Payload for Claude 3.5 Sonnet
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_bytes}}, {"type": "text", "text": prompt}]}]
    })
    
    # Agent then processes response to trigger MVD Email or Voiceflow Webhook

```

---

## 4. Dashboard Integration (UI/UX)

* **Sentinel Tab:** A new navigation item in the OneWay dashboard.
* **Reporting Timeline:** A list view showing "Reported Violations" with status tags: `Verified`, `Emailed to MVD`, or `Call Dispatched`.
* **The Registry (Internal):** A secure table for the "Car-to-Phone" database used for the parking assistant feature.

---

## 5. Metadata & Compliance (Important)

| Requirement | Logic |
| --- | --- |
| **Image Integrity** | Bedrock must check for consistent lighting and pixel noise to flag deepfakes. |
| **Data Privacy** | The registry of owner numbers must be encrypted and accessible only via the automated caller trigger. |
| **MVD Formatting** | Emails must adhere to the official format required by Kerala MVD for public complaints. |