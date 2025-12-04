# Expense Processing Agent Workflow

This project contains a LangGraph-based agent workflow to automatically process meal receipts, validate them against company policy, and route exceptions for manager approval.

Overview
--------
- `final_agent_v1.py`: Main workflow implementation. Uses LangGraph to orchestrate agents:
  - `policy_parser` - Reads policy DOCX and extracts rules.
  - `receipt_parser` - Calls `image_parser.get_receipt_details` to perform OCR and normalize results.
  - `policy_validator` - Applies policy rules and data quality checks; non-conforming receipts become exceptions.
  - `exception_router` - Human-in-the-loop manager approval; collects decision and comments.

- `image_parser.py`: Wrapper around a hypothetical `receipt_ocr` package to extract structured JSON from receipt images using an LLM-based OCR/processor.


Running
-------
- Place receipt images in `data/`.
- Update `POLICY_DOC_PATH` in `final_agent_v1.py` to point to your policy DOCX.
- Run:
  python src/agents/final_agent_v1.py

Outputs
-------
- `Expense_Status_Report.xlsx` with two sheets: `Expense Details` and `Exceptions`.

Design Details
--------------
- State flow: `policy_parser` -> `receipt_parser` -> `policy_validator` -> [if exception] `exception_router` -> back to `policy_validator` for next item.
- `get_receipt_details` should return a JSON object matching the schema defined in `image_parser.py`.


