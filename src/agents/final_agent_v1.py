"""
final_agent_v1.py

Overview:
This script implements a LangGraph-based agent workflow for automated meal expense processing
and manager exception handling. The workflow stages are:
  1. policy_parser     - Read and parse company policy document (DOCX).
  2. receipt_parser    - Use image_parser.get_receipt_details to OCR each receipt image
                         and normalize the JSON output into a receipt dict.
  3. policy_validator  - Validate each receipt against the parsed policy rules and
                         basic data quality checks. Non-conforming receipts are
                         recorded and routed to manager review (exceptions).
  4. exception_router  - Human-in-the-loop manager approval for exceptions. The
                         manager provides approval status and comments which are
                         recorded in both exceptions and processed expenses.

Design notes:
- State is carried through the LangGraph StateGraph as a TypedDict named ExpenseState.
- All records appended to processed_expenses and exceptions are plain Python dicts
  and later converted into pandas DataFrames for Excel export.
- Policy validation uses a simple hardcoded default policy (meal limit) if the DOCX
  cannot be read; this is easily extensible to richer rule parsing.

The file is intentionally documented with comments for each function; see in-file
comments for more details about each step.
"""

import pandas as pd
from datetime import datetime
import numpy as np
import os
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from docx import Document
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.image_parser import get_receipt_details

# Load environment variables
load_dotenv()

# --- SETUP ---
IMAGE_DIR = "/Users/sriramgona/Desktop/expense_project_finalcode/data"
POLICY_DOC_PATH = "/Users/sriramgona/Downloads/expense_project/files/company_policy.docx"
OUTPUT_FILE = "Expense_Status_Report.xlsx"
os.makedirs(IMAGE_DIR, exist_ok=True)

# --- STATE DEFINITIONS ---
class Receipt(TypedDict):
    receipt_id: str
    file_name: str
    merchant_name: str
    merchant_address: str
    merchant_phone: str
    subtotal: float
    taxes: float
    tips: float
    total_amount: float
    submission_date: str
    submitted_by: str
    requires_review: bool

class Policy(TypedDict):
    meal_limit_per_person: float
    required_fields: List[str]
    requires_manager_approval: bool

class ExpenseState(TypedDict):
    image_paths: List[str]
    policy_doc_path: str
    parsed_policy: Policy
    receipts: List[Receipt]
    processed_expenses: List[Dict[str, Any]]
    exceptions: List[Dict[str, Any]]
    current_receipt_index: int
    next_step: Literal["validate_receipt", "route_exception", "complete"]

# --- AGENT IMPLEMENTATIONS ---

def receipt_parser(state: ExpenseState) -> ExpenseState:
    """
    Parses receipts using OCR to extract structured data using image_parser.
    """
    print("--- [AGENT: Receipt Parser] ---")
    receipts = []
    
    for i, image_path in enumerate(state["image_paths"]):
        try:
            # Process receipt using image_parser
            ocr_result = get_receipt_details(image_path)
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            receipt = {
                "receipt_id": ocr_result.get('Expense ID', f"RCP{i+1:03}"),
                "file_name": os.path.basename(image_path),
                "merchant_name": ocr_result.get('Merchant Name', 'Unknown Merchant'),
                "merchant_address": ocr_result.get('Merchant Address', 'N/A'),
                "merchant_phone": ocr_result.get('Merchant Phone', 'N/A'),
                "subtotal": float(ocr_result.get('Subtotal', 0.0)),
                "taxes": float(ocr_result.get('Taxes', 0.0)),
                "tips": float(ocr_result.get('Tips', 0.0)),
                "total_amount": float(ocr_result.get('Total Amount', 0.0)),
                "submission_date": current_time,
                "submitted_by": ocr_result.get('Submitted By', 'System'),
                "expense_date": ocr_result.get('Submission Date', current_time),
                "requires_review": False
            }
            
            # Flag for review if any required field is missing
            if not all([
                receipt['merchant_name'] != 'Unknown Merchant',
                receipt['total_amount'] > 0,
                receipt['subtotal'] > 0
            ]):
                receipt['requires_review'] = True
                
            receipts.append(receipt)
            print(f"Successfully parsed receipt {receipt['receipt_id']} from {receipt['file_name']}")
            
        except Exception as e:
            print(f"Error processing receipt {image_path}: {str(e)}")
            # Add a placeholder receipt that requires review
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            receipt = {
                "receipt_id": f"RCP{i+1:03}",
                "file_name": os.path.basename(image_path),
                "merchant_name": "OCR_FAILED",
                "merchant_address": "N/A",
                "merchant_phone": "N/A",
                "subtotal": 0.0,
                "taxes": 0.0,
                "tips": 0.0,
                "total_amount": 0.0,
                "submission_date": current_time,
                "submitted_by": "System",
                "expense_date": current_time,
                "requires_review": True
            }
            receipts.append(receipt)
    
    return {
        "receipts": receipts,
        "current_receipt_index": 0,
        "next_step": "validate_receipt"
    }

def policy_parser(state: ExpenseState) -> ExpenseState:
    """
    Extracts policy rules from the policy document.
    """
    print("--- [AGENT: Policy Parser] ---")
    
    try:
        doc = Document(state["policy_doc_path"])
        policy_text = " ".join([p.text for p in doc.paragraphs])
    except:
        print("Warning: Using default policy rules")
        policy_text = "Default policy"
    
    parsed_policy = {
        "meal_limit_per_person": 35.0,
        "required_fields": ["date", "merchant", "items", "total"],
        "requires_manager_approval": True
    }
    
    return {"parsed_policy": parsed_policy}

def policy_validator(state: ExpenseState) -> ExpenseState:
    """
    Validates receipts against policy rules and document requirements.
    """
    print("--- [AGENT: Policy Validator] ---")
    
    idx = state["current_receipt_index"]
    if idx >= len(state["receipts"]):
        return {"next_step": "complete"}
    
    receipt = state["receipts"][idx]
    policy = state["parsed_policy"]
    
    is_compliant = True
    validation_notes = []
    
    # Validate required fields from policy document
    missing_fields = []
    if receipt["merchant_name"] in ["Unknown Merchant", "OCR_FAILED"]:
        missing_fields.append("merchant name")
    if receipt["total_amount"] <= 0:
        missing_fields.append("total amount")
    if receipt["subtotal"] <= 0:
        missing_fields.append("itemized subtotal")
        
    if missing_fields:
        is_compliant = False
        validation_notes.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate total amount against policy limit
    if receipt["total_amount"] > policy["meal_limit_per_person"]:
        is_compliant = False
        validation_notes.append(f"Amount ${receipt['total_amount']} exceeds limit ${policy['meal_limit_per_person']}")
    
    # Check if receipt requires review from OCR
    if receipt["requires_review"]:
        is_compliant = False
        validation_notes.append("Receipt flagged for review due to data quality issues")
    expense_record = {
        "Expense ID": receipt["receipt_id"],
        "Submission Date": receipt["submission_date"],
        "Submitted By": receipt["submitted_by"],
        "Expense Date": receipt["expense_date"],
        "Merchant Name": receipt["merchant_name"],
        "Merchant Address": receipt["merchant_address"],
        "Merchant Phone": receipt["merchant_phone"],
        "Subtotal": receipt["subtotal"],
        "Taxes": receipt["taxes"],
        "Tips": receipt["tips"],
        "Total Amount": receipt["total_amount"],
        "Policy Validation": "Exception" if not is_compliant else "Conform",
        "Approval Status": "Pending" if not is_compliant else "Approved",
        "Approval Date": receipt["submission_date"] if is_compliant else None,
        "Receipt Image": receipt["file_name"]
    }
    
    new_processed_expenses = state.get("processed_expenses", [])
    new_processed_expenses.append(expense_record)
    
    next_step = "route_exception" if not is_compliant else "validate_receipt"
    
    if not is_compliant:
        # Create a detailed exception record for manager review
        exception_record = {
            "Expense ID": receipt["receipt_id"],
            "Exception Reason": " | ".join(validation_notes),
            "Approval Status": "Pending",
            "Approved By": None,
            "Approval Date": None,
            "Approver Comments": "Pending manager review for policy exceptions"
        }
        new_exceptions = state.get("exceptions", [])
        new_exceptions.append(exception_record)
        return {
            "processed_expenses": new_processed_expenses,
            "exceptions": new_exceptions,
            "current_receipt_index": idx,
            "next_step": next_step
        }
    
    return {
        "processed_expenses": new_processed_expenses,
        "current_receipt_index": idx + 1,
        "next_step": next_step
    }

def exception_router(state: ExpenseState) -> ExpenseState:
    """
    Routes exceptions to manager and simulates approval decisions.
    """
    print("--- [AGENT: Exception Router] ---")
    
    exceptions = state.get("exceptions", [])
    processed_expenses = state.get("processed_expenses", [])
    
    for exc in exceptions:
        if exc["Approval Status"] == "Pending":
            # Determine approval based on exception type
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get manager's approval through human interaction
            status, comments = get_manager_approval(
                exc["Expense ID"], 
                exc["Exception Reason"]
            )
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update exception record with manager's decision
            exc["Approval Status"] = status
            exc["Approver Comments"] = comments
            if status == "Approved":
                exc["Approved By"] = "Manager"
                exc["Approval Date"] = current_time
            else:
                exc["Approved By"] = "Manager"
                exc["Approval Date"] = current_time
            
            # Update corresponding expense record
            for exp in processed_expenses:
                if exp["Expense ID"] == exc["Expense ID"]:
                    exp["Approval Status"] = status
                    exp["Policy Validation"] = "Exception"  # Keep Exception status even if approved
                    exp["Approval Date"] = current_time
                    break
    
    return {
        "exceptions": exceptions,
        "processed_expenses": processed_expenses,
        "current_receipt_index": state["current_receipt_index"] + 1,
        "next_step": "validate_receipt"
    }

def get_manager_approval(expense_id: str, exception_reason: str) -> tuple:
    """
    Get manager's approval decision through human interaction.
    Returns a tuple of (approval_status, comments)
    """
    print(f"\n=== Manager Review Required for Expense {expense_id} ===")
    print(f"Exception Reason: {exception_reason}")
    
    while True:
        status = input("\nEnter approval status (Approved/Rejected): ").strip().capitalize()
        if status in ["Approved", "Rejected"]:
            break
        print("Invalid status. Please enter 'Approved' or 'Rejected'")
    
    comments = input("Enter approval comments: ").strip()
    if not comments:
        comments = "Approved by manager" if status == "Approved" else "Rejected by manager"
    
    return status, comments

# --- WORKFLOW DEFINITION ---

def expense_router(state: ExpenseState) -> str:
    """Routes to the next step based on state."""
    return state["next_step"]

# Create the workflow graph
workflow = StateGraph(ExpenseState)

# Add nodes
workflow.add_node("receipt_parser", receipt_parser)
workflow.add_node("policy_parser", policy_parser)
workflow.add_node("policy_validator", policy_validator)
workflow.add_node("exception_router", exception_router)

# Set up the workflow
workflow.set_entry_point("policy_parser")
workflow.add_edge("policy_parser", "receipt_parser")
workflow.add_edge("receipt_parser", "policy_validator")

# Add conditional edges
workflow.add_conditional_edges(
    "policy_validator",
    expense_router,
    {
        "validate_receipt": "policy_validator",
        "route_exception": "exception_router",
        "complete": END
    }
)

workflow.add_conditional_edges(
    "exception_router",
    expense_router,
    {
        "validate_receipt": "policy_validator",
        "complete": END
    }
)

# Compile the workflow
app = workflow.compile()

if __name__ == "__main__":
    # Scan for receipt images
    print(f"\nScanning directory: {IMAGE_DIR}")
    
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(IMAGE_EXTENSIONS)]
    image_paths = [os.path.join(IMAGE_DIR, f) for f in image_files]
    
    if not image_paths:
        print("Error: No receipt images found in the directory.")
    else:
        print(f"Found {len(image_paths)} receipts to process")
        
        # Initialize and run workflow
        initial_state = {
            "policy_doc_path": POLICY_DOC_PATH,
            "image_paths": image_paths,
            "receipts": [],
            "current_receipt_index": 0,
            "processed_expenses": [],
            "exceptions": []
        }
        
        final_state = app.invoke(initial_state)
        
        # Export results to Excel
        try:
            # Create expense details dataframe
            df_expenses = pd.DataFrame(final_state["processed_expenses"])
            
            # Create exceptions dataframe
            df_exceptions = pd.DataFrame(final_state["exceptions"])
            
            # Export to Excel
            with pd.ExcelWriter(OUTPUT_FILE, engine='xlsxwriter') as writer:
                # Configure the workbook
                workbook = writer.book
                money_format = workbook.add_format({'num_format': '$#,##0.00'})
                datetime_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
                
                # Write Expense Details sheet
                df_expenses.to_excel(writer, sheet_name='Expense Details', index=False)
                worksheet = writer.sheets['Expense Details']
                
                # Format columns
                for col_num, column in enumerate(df_expenses.columns):
                    if column in ['Subtotal', 'Taxes', 'Tips', 'Total Amount']:
                        worksheet.set_column(col_num, col_num, 12, money_format)
                    elif column in ['Submission Date', 'Expense Date', 'Approval Date']:
                        worksheet.set_column(col_num, col_num, 20, datetime_format)
                    else:
                        worksheet.set_column(col_num, col_num, 15)
                
                # Write Exceptions sheet
                df_exceptions.to_excel(writer, sheet_name='Exceptions', index=False)
                worksheet = writer.sheets['Exceptions']
                
                # Format columns
                for col_num, column in enumerate(df_exceptions.columns):
                    if column in ['Approval Date']:
                        worksheet.set_column(col_num, col_num, 20, datetime_format)
                    elif column == 'Exception Reason':
                        worksheet.set_column(col_num, col_num, 40)
                    elif column == 'Approver Comments':
                        worksheet.set_column(col_num, col_num, 30)
                    else:
                        worksheet.set_column(col_num, col_num, 15)
            
            print(f"\n✅ Report generated successfully: {OUTPUT_FILE}")
            
            # Print summary
            print("\n--- Expense Details Summary ---")
            print(df_expenses[["Expense ID", "Merchant Name", "Total Amount", "Policy Validation", "Approval Status"]])
            
            if not df_exceptions.empty:
                print("\n--- Exceptions Summary ---")
                print(df_exceptions[["Expense ID", "Exception Reason", "Approval Status", "Approver Comments"]])
                
        except Exception as e:
            print(f"\n❌ Error generating report: {str(e)}")


