# Multi-Agent Expense Processing Workflow with LangGraph

A sophisticated, production-ready expense management system that demonstrates advanced multi-agent orchestration using LangGraph. This project showcases automated expense processing, policy validation, and human-in-the-loop manager approvals through an elegant state machine architecture.

## 🎯 Project Overview

This system implements an intelligent, multi-stage workflow for processing meal expense receipts with automatic policy validation and exception handling. Built with LangGraph's StateGraph framework, it demonstrates practical applications of agentic AI workflows in enterprise automation.

### Key Capabilities

- **Automated Document Processing**: OCR-based receipt extraction from images
- **Policy-Driven Validation**: Dynamic rule parsing from company policy documents
- **Exception Management**: Human-in-the-loop approval workflow for policy violations
- **Audit Trail**: Complete tracking of all expenses, validations, and manager decisions
- **Excel Export**: Professional reporting with separate sheets for processed expenses and exceptions

## 🏗️ Architecture

The workflow is implemented as a directed graph with four specialized agent nodes:

```
┌─────────────────┐
│ policy_parser   │  Parse company policy rules from DOCX
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ receipt_parser  │  OCR and normalize receipt data from images
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│policy_validator │  Validate expenses against policy rules
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│exception_router │  Human-in-the-loop manager approval
└─────────────────┘
```

### Agent Responsibilities

#### 1. Policy Parser
- Reads company policy documents (DOCX format)
- Extracts and structures policy rules
- Falls back to sensible defaults if document parsing fails
- Prepares validation criteria for downstream agents

#### 2. Receipt Parser
- Processes receipt images using OCR (via `image_parser.get_receipt_details`)
- Normalizes extracted data into standardized JSON format
- Handles multiple receipt formats and layouts
- Ensures data quality and completeness

#### 3. Policy Validator
- Cross-references expenses against parsed policy rules
- Performs data quality checks (missing fields, format validation)
- Identifies policy violations and non-conforming submissions
- Routes compliant expenses to processing and exceptions to review

#### 4. Exception Router
- Implements human-in-the-loop approval workflow
- Captures manager decisions (approve/reject) with comments
- Maintains audit trail of all exception handling
- Updates expense records with approval status

## 🔧 Technical Implementation

### State Management

The workflow uses a strongly-typed state object (`ExpenseState`) implemented as a TypedDict:

```python
class ExpenseState(TypedDict):
    policy_text: str
    receipt_images: List[str]
    processed_expenses: List[Dict]
    exceptions: List[Dict]
    # ... additional state fields
```

**Design Benefits:**
- Type safety and IDE autocomplete support
- Clear data contracts between agents
- Immutable state transitions for debugging
- Easy serialization for persistence

### Data Flow

1. **Input**: Policy document (DOCX) + Receipt images (PNG/JPG)
2. **Processing**: Each agent transforms state through pure functions
3. **Output**: Excel workbook with processed expenses and exceptions

All intermediate results are stored as plain Python dictionaries for flexibility, then converted to pandas DataFrames for professional Excel export.

### Error Handling

- **Graceful Degradation**: Falls back to default policies if document parsing fails
- **Validation Gates**: Each stage validates input before processing
- **Exception Tracking**: All errors and policy violations are logged for review
- **Human Oversight**: Manager review ensures no valid expense is lost

## 🚀 Key Features

### 1. Extensible Policy Framework
The policy parser is designed for easy extension:
- Add new rule types without modifying core logic
- Support for complex conditional policies
- Version control for policy documents
- Audit trail of policy changes

### 2. Robust OCR Integration
Receipt parsing handles real-world variability:
- Multiple receipt formats and layouts
- Handling of poor image quality
- Data normalization and standardization
- Confidence scoring for OCR results

### 3. Human-in-the-Loop Design
Manager approval workflow includes:
- Clear presentation of policy violations
- Context-rich decision making interface
- Comments and justification tracking
- Approval/rejection with audit trail

### 4. Production-Ready Output
Excel export includes:
- **Processed Expenses**: All approved and compliant expenses
- **Exceptions**: Policy violations with manager decisions
- Formatted tables with proper headers
- Easy integration with existing financial systems

## 💡 Technical Depth Demonstrated

This project showcases several advanced concepts:

### Multi-Agent Orchestration
- **State Graph Design**: Leveraging LangGraph's StateGraph for complex workflows
- **Agent Coordination**: Sequential and conditional routing between specialized agents
- **State Persistence**: Maintaining context across multiple processing stages

### Enterprise Integration Patterns
- **Document Processing**: Real-world document parsing and OCR
- **Policy as Code**: Translating business rules into executable validation logic
- **Human-in-the-Loop**: Balancing automation with human oversight
- **Data Export**: Professional reporting for business stakeholders

### Software Engineering Best Practices
- **Type Safety**: TypedDict for compile-time type checking
- **Separation of Concerns**: Each agent has a single, well-defined responsibility
- **Extensibility**: Easy to add new validation rules or processing steps
- **Testability**: Pure functions for each agent enable comprehensive testing

## 📋 Use Cases

This workflow architecture is applicable to:

- **Expense Management**: Automated processing of employee expense claims
- **Invoice Processing**: Vendor invoice validation and approval workflows
- **Compliance Checking**: Regulatory compliance validation in document processing
- **Quality Assurance**: Multi-stage validation with exception handling
- **Approval Workflows**: Any process requiring human oversight with automated screening

## 🔄 Workflow Execution

```python
# Initialize the workflow
workflow = create_expense_workflow()

# Define initial state
initial_state = {
    "policy_document": "company_policy.docx",
    "receipt_images": ["receipt1.jpg", "receipt2.jpg"],
    "processed_expenses": [],
    "exceptions": []
}

# Execute the workflow
final_state = workflow.invoke(initial_state)

# Export results
export_to_excel(final_state)
```

## 🎓 Learning Outcomes

Building this project demonstrates proficiency in:

- **LangGraph Framework**: Advanced state machine orchestration
- **Multi-Agent Systems**: Coordinating specialized agents with different responsibilities
- **Document AI**: OCR, parsing, and information extraction
- **Workflow Design**: Building production-ready business process automation
- **Python Development**: Type hints, dataclasses, and modern Python practices

## 🛠️ Technology Stack

- **LangGraph**: State graph orchestration and agent coordination
- **Python 3.8+**: Core implementation language
- **pandas**: Data manipulation and Excel export
- **python-docx**: Policy document parsing
- **Custom OCR Module**: Receipt image processing (`image_parser`)

## 📈 Future Enhancements

Potential extensions to demonstrate additional capabilities:

- **LLM-Powered Policy Parsing**: Use LLMs to extract complex rules from natural language
- **Multi-Modal Validation**: Combine OCR with image analysis for fraud detection
- **Parallel Processing**: Process multiple receipts concurrently for scalability
- **Real-Time Dashboard**: Web UI for manager approval workflows
- **Machine Learning**: Learn patterns from historical approvals to reduce exceptions
- **Integration APIs**: REST endpoints for enterprise system integration

## 📄 License

[Your License Here]

## 🤝 Contributing

This is a demonstration project showcasing technical capabilities in multi-agent workflows. Feedback and suggestions are welcome!

## 📧 Contact

[Your Contact Information]

---

**Note**: This project demonstrates advanced concepts in agentic AI workflows and is designed to showcase technical depth in multi-agent orchestration, state management, and enterprise automation patterns.
