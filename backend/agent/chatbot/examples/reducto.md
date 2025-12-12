Reducto API Quickstart Notebook - Python
Welcome! This notebook walks you through the basics of using Reducto’s Python SDK.
Following the quickstart guide, you’ll upload a sample intake form, parse it, and extract key information.
By the end, you’ll know how to:
Parse a document
Apply optional configurations
Reuse the job_id to run an extraction

1. Download a document and Reducto's SDK
   Find our Python SDK here, as well as your Reducto API key under "API Keys" in your Reducto Studio account.
   !wget https://cdn.reducto.ai/Patient-Intake-Form.pdf

# Install Reducto from PyPI

!pip install reductoai
Show hidden output
from reducto import Reducto
from google.colab import userdata

# Find your Reducto API key in your Studio account

client = Reducto(api_key=userdata.get('REDUCTO_API_KEY'), timeout=300)
 2. Run Parse!
The fastest way to get started is to call our Parse endpoint with no specified configurations. Parse takes in your document, and reads it
like a human, returning the data in a structured JSON format.
The result gives you information about each block's content, type, bounding box coordinates, and much more.
You can also see the job_id which is useful for chaining endpoint calls and debugging.
from pathlib import Path

# Upload the patient intake form pdf

upload = client.upload(file=Path("Patient-Intake-Form.pdf"))

# Run Parse with default configurations

parsed_result = client.parse.run(document_url=upload)
print(parsed_result.to_json())
Show hidden output
 3. Add custom configurations
All of our endpoints have optional configurations that can change the outputs. See our best practices for each endpoint for some
common tips on how to improve your output quality.
In this emergency responder intake form example:
There is a lot of handwriting, so we'll enable increase.
We'll use the page_range There are checkboxes, so we'll enable agentic ocr mode which is great for higher handwriting accuracy with a small latency
config to only parse the first page.
enable_checkboxes.
parse_with_configs = client.parse.run(
document_url=upload,
options={
"ocr_mode": "agentic" # Agentic OCR mode
},
https://colab.research.google.com/drive/1xagcIu4FQT0PE4vugBKlZam07peU
\_\_
8R?usp=sharing#scrollTo=yFXFbGO4VxqQ&printMode=true 1/3
12/12/25, 7:33 AM Reducto Python Quickstart.ipynb - Colab

advanced_options={
"page_range": {
"start": 1, # 1-indexed page number
"end": 1,
}
},
experimental_options={
"enable_checkboxes": True # Enable checkbox detection
}
)
print(parse_with_configs.to_json())
Show hidden output 4. Call Extract using the Parse job_id
Extract is when you'd like to get specific data off of a file. You define a schema and system prompt that is then passed into the endpoint
call.
Goal: Get the form's basic information like responder name, last 4 SSN, and date.
Your schema might look like this:
import json

# Sample schema for the form's information

schema= {
"type": "object",
"properties": {
"date": {
"type": "string",
"description": "Date of the first responder record."
},
"last_4": {
"type": "string",
"description": "Last 4 digits of the responder's identifier."
},
"name": {
"type": "object",
"properties": {
"first": {
"type": "string",
"description": "Responder's first name."
},
"last": {
"type": "string",
"description": "Responder's last name."
}
},
"required": [
"first",
"last"
]
}
},
"required": [
"date",
"last_4",
"name"
]
}
Next, pass your schema into the extraction call together with the results instead of running the parse again.
job_id from the earlier parse step. This way, you reuse the parse
This technique is called pipelining — chaining endpoint calls to save credits and improve efficiency.
parse_job_id = parse_with_configs.job_id
extract_result = client.extract.run(
document_url=f"jobid://{parse_job_id}"
schema=schema
,
)
https://colab.research.google.com/drive/1xagcIu4FQT0PE4vugBKlZam07peU
\_\_
8R?usp=sharing#scrollTo=yFXFbGO4VxqQ&printMode=true 2/3
12/12/25, 7:33 AM Reducto Python Quickstart.ipynb - Colab
print(json.dumps(extract_result.result, indent=4))
[
{
"date": "01-JAN-24",
"last_4": "0007",
"name": {
"first": "Hand",
"last": "Scanner"
}
}
]
🎉 Congrats! You just built your first pipeline.
In this tutorial, you:
Parsed a document
Applied optional configurations
Reused the job_id to run an extraction without re-parsing
You now have the foundation for chaining endpoints together—what we call pipelining. With this approach, you can extend pipelines to
handle splitting, editing, or more advanced extraction tasks.
What's next
Try edit to automatically update or fill out documents
Explore other configurations, such as table formatting options.
👉 Check out the full Reducto documentation to continue building.
https://colab.research.google.com/drive/1
