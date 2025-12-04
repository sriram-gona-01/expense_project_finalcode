import os

from receipt_ocr.processors import ReceiptProcessor
from receipt_ocr.providers import OpenAIProvider
from dotenv import load_dotenv
load_dotenv()


def get_receipt_details(image_path):
    # Initialize the provider
    provider = OpenAIProvider(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://api.openai.com/v1/")
    print(os.environ.get("OPENAI_API_KEY"))
    # Initialize the processor
    processor = ReceiptProcessor(provider)

    # Define the JSON schema for extraction
    json_schema = {
        "Expense ID": "string",
        "Merchant Name": "string",
        "Merchant Address": "string",
        "Merchant Phone": "number",
        "Subtotal": "number",
        "Taxes": "number",
        "Tips": "number",
        "Total Amount": "number",
        "Submission Date": "string",
        "Submitted By": "string"
    }

    # Process the receipt
    result = processor.process_receipt(image_path, json_schema, "gpt-5-mini")

    print(result)


    # result = processor.process_receipt(
    #     image_path,
    #     json_schema,
    #     "gpt-4.1",
    #     response_format_type="json_object"  # or "json_schema", "text"
    # )
    return result


if __name__ == "__main__":
    image_path = r"C/Users/sriramgona/Desktop/expense_project_finalcode/data/R2.jpg"
    res = get_receipt_details(image_path)
    print(res)