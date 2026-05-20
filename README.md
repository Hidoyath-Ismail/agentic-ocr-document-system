# Agentic OCR Document Intake System

An AI-assisted document intake pipeline for invoices, receipts, and purchase orders using Python, LangGraph, Streamlit, OCR fallback, deterministic validation, controlled LLM fallback, human-in-the-loop review, and audit-ready JSON outputs.

## Overview

The Agentic OCR Document Intake System is designed to process business documents such as invoices, receipts, and purchase orders. Instead of relying only on OCR, the system uses a multi-step agentic workflow to extract text, classify document information, validate required fields, trigger fallback extraction when needed, and generate structured outputs.

This project was built to demonstrate production-oriented AI workflow design, with a focus on traceability, validation, reviewability, and audit-ready outputs.

## Detailed Case Study

For a deeper explanation of the project design, workflow, validation strategy, LLM fallback logic, human review process, and audit-ready output structure, see the full case study:

[Read the full case study](CASE_STUDY.md)

## Why This Project Matters

This project demonstrates more than basic OCR. It shows how document automation can be designed with controlled AI usage, validation checkpoints, human review, and auditability.

Instead of sending every document directly to an LLM, the system first attempts deterministic extraction and validation. The LLM is used only as a fallback when required, and the output is re-validated before final approval. This design is especially relevant for quality-sensitive and regulated environments where traceability, reviewability, and reliable outputs are important.

## Problem Statement

Manual document intake is time-consuming and error-prone. Many document automation systems extract text but do not provide enough validation, fallback logic, or auditability for real-world business workflows.

This project addresses that gap by combining:

- PDF text extraction
- OCR fallback for scanned or image-based documents
- deterministic field extraction
- validation rules
- LLM-assisted fallback extraction
- human-in-the-loop correction
- clean and audit-ready JSON outputs

## Key Features

- Upload and preview PDF documents through a Streamlit interface
- Extract text from digital PDFs using PDF parsing
- Trigger OCR fallback when direct text extraction is insufficient
- Extract structured fields such as vendor name, date, total amount, and document type
- Validate extracted fields using deterministic rules
- Use LLM fallback only when validation fails or confidence is low
- Allow human review and correction before final approval
- Save clean JSON output for downstream use
- Save audit JSON output with traceability details and processing notes

## Agentic Workflow

The workflow is orchestrated using LangGraph and follows a controlled sequence:

```text
ingest_document
        ↓
extract_text_if_possible
        ↓
OCR fallback if needed
        ↓
structured_extraction
        ↓
validation
        ↓
LLM fallback if validation fails
        ↓
validation
        ↓
human review if needed
        ↓
finalize and save outputs
```

## Architecture

The project separates the workflow into single-responsibility components:
```text
src/
├── schemas/
│   └── extraction.py
├── tools/
│   ├── pdf_text_extractor.py
│   ├── ocr_pdf_extractor.py
│   ├── deterministic_extractor.py
│   ├── llm_extractor.py
│   ├── merge_utils.py
│   └── validator.py
├── web_app/
│   └── streamlit_app.py
└── workflow/
    ├── graph.py
    └── state.py
```

## Tech Stack
Python
Streamlit
LangGraph
Pydantic
pypdf
pdf2image
pytesseract
Tesseract OCR
Poppler
OpenAI API
JSON-based audit output

## Validation and Auditability

A key design goal of this project is controlled AI usage. The system first attempts deterministic extraction and validation before using LLM fallback. The LLM is used only when required, and validation is rerun after fallback extraction.

The system also maintains audit notes across the workflow so that the processing path is traceable. This makes the project especially relevant for regulated or quality-sensitive environments where explainability, reviewability, and validation matter.

## Human-in-the-Loop Review

When extracted data is incomplete or validation fails, the Streamlit interface allows the user to review and correct fields before finalizing the document. This prevents the system from blindly accepting low-confidence AI output.

## Sample Outputs

The system generates two types of JSON outputs:

Clean JSON — structured document data suitable for downstream systems
Audit JSON — includes processing metadata, validation status, audit notes, and traceability details

## Screenshots

The screenshots below show the end-to-end LLM fallback route, including document upload, PDF preview, extraction, validation feedback, human review, approval, and final JSON output.

### 1. Upload Document

![Upload screen](screenshots/01-upload-screen.png)

### 2. PDF Preview

![PDF preview](screenshots/02-pdf-preview.png)

### 3. LLM Fallback Extraction

![LLM fallback extraction](screenshots/03-llm-fallback-extraction.png)

### 4. Audit Trail and Validation Errors

![Audit trail and validation errors](screenshots/04-audit-trail-validation-errors.png)

### 5. Human Review and Approved Output

![Human review approved output](screenshots/05-human-review-approved-output.png)

### 6. Reviewer Details

![Reviewer details](screenshots/06-reviewer-details.png)

### 7. Final JSON Output Link

![Final JSON output link](screenshots/07-final-json-output-link.png)

## How to Run Locally

Clone the repository:

git clone https://github.com/Hidoyath-Ismail/agentic-ocr-document-system.git
cd agentic-ocr-document-system

Create and activate a virtual environment:

python -m venv .venv
.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create a .env file based on .env.example and add the required environment variables.

Run the Streamlit app:

streamlit run src/web_app/streamlit_app.py

## Future Improvements

- Add sample synthetic documents for demo use
- Add unit tests for validation and extraction rules
- Add deployment support
- Add document type-specific extraction strategies
- Add confidence scoring for extracted fields
- Add support for more document formats

## What I Learned

This project helped me practice designing an AI workflow that is not just a prototype, but a more reliable document processing pipeline. I learned how to combine deterministic logic, OCR, LLM fallback, validation rules, human review, and audit trail generation into a single end-to-end system.
