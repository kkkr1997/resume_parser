import os
import json
import csv
from typing import Dict, Optional, List, Any, Tuple
from docx import Document
import PyPDF2
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

class ResumeParser:
    def __init__(self):
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key not found. Please set it in the .env file.")
        
        self.system_prompt = """
        You are a resume parser. Extract ONLY the following information from the resume and return it in this exact JSON format:
        {
            "name": "candidate full name",
            "contact": {
                "email": "email address if found",
                "phone": "phone number if found"
            },
            "skills": ["skill1", "skill2", "etc"],
            "experience": [
                {
                    "job_title": "job title",
                    "company_name": "company name",
                    "duration_dates": "employment period",
                    "key_responsibilities": ["responsibility1", "responsibility2", "etc"]
                }
            ]
        }
        
        Important rules:
        1. Return ONLY valid JSON, no other text
        2. For missing information, use empty strings or empty arrays
        3. For skills, return a flat array of ALL skills found (technical, soft skills, etc)
        4. Keep descriptions brief and concise
        5. Do not categorize or classify the skills
        """

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            return None

    def extract_text_from_docx(self, docx_path: str) -> Optional[str]:
        try:
            doc = Document(docx_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            print(f"Error extracting text from DOCX {docx_path}: {str(e)}")
            return None

    def extract_text_from_txt(self, txt_path: str) -> Optional[str]:
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file {txt_path}: {str(e)}")
            return None
            
    def extract_information(self, text: str) -> Dict[str, Any]:
        """Extract information from resume text using OpenAI's GPT model."""
        messages = [
            {"role": "system", "content": f"{self.system_prompt}\nRespond ONLY with a valid JSON object."}, 
            {"role": "user", "content": f"Please extract information from this resume:\n\n{text}"}
        ]

        try:
            # Set a timeout for the API call
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Using GPT-3.5 for faster response
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            try:
                response_text = response.choices[0].message.content.strip()
                # Remove any markdown code block markers if present
                response_text = response_text.replace('```json', '').replace('```', '').strip()
                print(f"\nOpenAI Response:\n{response_text}\n")
                parsed_info = json.loads(response_text)
                
                # Ensure the response has the expected structure
                if not isinstance(parsed_info, dict):
                    print("Error: OpenAI response is not a dictionary")
                    return {}
                
                # Validate and clean up the response
                cleaned_info = {
                    'name': str(parsed_info.get('name', '')).strip(),
                    'contact': {
                        'email': str(parsed_info.get('contact', {}).get('email', '')).strip(),
                        'phone': str(parsed_info.get('contact', {}).get('phone', '')).strip()
                    }
                }
                
                # Handle skills
                skills = parsed_info.get('skills', [])
                if isinstance(skills, list):
                    cleaned_info['skills'] = [str(skill).strip() for skill in skills if skill]
                else:
                    cleaned_info['skills'] = []
                
                # Handle experience
                experience = parsed_info.get('experience', [])
                if isinstance(experience, list):
                    cleaned_experience = []
                    for exp in experience:
                        if isinstance(exp, dict):
                            cleaned_exp = {
                                'job_title': str(exp.get('job_title', '')).strip(),
                                'company_name': str(exp.get('company_name', '')).strip(),
                                'duration_dates': str(exp.get('duration_dates', '')).strip(),
                                'key_responsibilities': [str(resp).strip() for resp in exp.get('key_responsibilities', []) if resp]
                            }
                            if cleaned_exp['job_title'] and cleaned_exp['company_name']:
                                cleaned_experience.append(cleaned_exp)
                    cleaned_info['experience'] = cleaned_experience
                else:
                    cleaned_info['experience'] = []
                
                return cleaned_info
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {str(e)}")
                print(f"Response text: {response_text}")
                return {}
            except Exception as e:
                print(f"Error processing OpenAI response: {str(e)}")
                return {}
        except openai.APITimeoutError:
            print("OpenAI API request timed out. Please try again.")
            return {}
        except openai.APIError as e:
            print(f"OpenAI API error: {str(e)}")
            return {}
        except Exception as e:
            print(f"Unexpected error calling OpenAI API: {str(e)}")
            return {}

    def flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten a nested dictionary by concatenating nested keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle lists of dictionaries
                if v and isinstance(v[0], dict):
                    for i, item in enumerate(v):
                        items.extend(self.flatten_dict(item, f"{new_key}_{i+1}", sep=sep).items())
                else:
                    items.append((new_key, ', '.join(str(x) for x in v) if v else ''))
            else:
                items.append((new_key, str(v) if v is not None else ''))
        return dict(items)

    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        # Get file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Extract text based on file type
        if ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif ext == '.docx':
            text = self.extract_text_from_docx(file_path)
        elif ext == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            print(f"Unsupported file format: {ext}")
            return {}

        if not text:
            print(f"Failed to extract text from {file_path}")
            return {}

        # Extract information using OpenAI
        parsed_info = self.extract_information(text)
        
        # Format skills for CSV output
        if 'skills' in parsed_info:
            skills = parsed_info.get('skills', [])
        # Flatten contact information
        if 'contact' in parsed_info:
            contact = parsed_info.pop('contact', {})
            parsed_info.update({
                'email': contact.get('email', ''),
                'phone': contact.get('phone', '')
            })
        
        # Format skills as a single string
        if 'skills' in parsed_info:
            skills = parsed_info.get('skills', [])
            if isinstance(skills, list):
                parsed_info['skills'] = ', '.join(str(skill) for skill in skills if skill)
            else:
                parsed_info['skills'] = ''
        
        # Format experience as a concise string
        if 'experience' in parsed_info:
            experience = parsed_info.pop('experience', [])
            exp_entries = []
            for exp in experience:
                if isinstance(exp, dict):
                    job_title = exp.get('job_title', '')
                    company = exp.get('company_name', '')
                    duration = exp.get('duration_dates', '')
                    if job_title and company:
                        exp_entries.append(f"{job_title} at {company} ({duration})")
            parsed_info['experience'] = ' | '.join(exp_entries) if exp_entries else ''
                
        return parsed_info

def process_single_resume(file_path: str) -> Dict[str, Any]:
    """Process a single resume file and return the parsed information."""
    parser = ResumeParser()
    try:
        print(f"Processing: {os.path.basename(file_path)}")
        parsed_info = parser.parse_resume(file_path)
        if parsed_info:
            print(f"Parsed information: {parsed_info}")
            parsed_info['filename'] = os.path.basename(file_path)
            print(type(parsed_info))
            append_to_csv(parsed_info)
            return parsed_info
    except Exception as e:
        print(f"Error processing {os.path.basename(file_path)}: {str(e)}")
    return None

def append_to_csv(parsed_info: Dict[str, Any], output_file: str = 'resume_details.csv'):
    """Append a single resume's information to the CSV file."""
    try:
        print(f"Processing: {parsed_info.get('name', 'unknown')}")

        # Extract contact info
        contact = parsed_info.get('contact', {})
        print(f"Contact: {contact}")
        print(f"before simplifying {parsed_info}")
        simplified_resume = {
            'filename': parsed_info.get('filename', ''),
            'Name': parsed_info.get('name', ''),
            'Email': parsed_info.get('email', ''),
            'Phone': parsed_info.get('phone', ''),
            'Skills': parsed_info.get('skills', []),
            'Experience': parsed_info.get('experience', [])
        }

        print(f"Final simplified_resume: {simplified_resume}")

        # Write to CSV
        fieldnames = ['filename', 'Name', 'Email', 'Phone', 'Skills', 'Experience']
        file_exists = os.path.exists(output_file)

        # Open file in append mode with proper encoding
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(simplified_resume)
            print(f"Successfully processed {simplified_resume['Name']}")
    except Exception as e:
        print(f"Error processing {parsed_info.get('name', 'unknown')} : {str(e)}")

def check_if_processed(filename: str, output_file: str) -> bool:
    """Check if a file has already been processed by looking for its filename in the CSV."""
    if not os.path.exists(output_file):
        return False
        
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            return filename in content
    except Exception as e:
        print(f"Error checking processed status: {str(e)}")
        return False

def main():
    # Get all resume files in the resumes directory
    resume_dir = 'resumes'
    if not os.path.exists(resume_dir):
        os.makedirs(resume_dir)
        print(f"Created '{resume_dir}' directory. Please place resume files there.")
        return
    
    # Get all resume files
    resume_files = [os.path.join(resume_dir, f) for f in os.listdir(resume_dir) 
                   if f.lower().endswith(('.pdf', '.docx', '.txt'))]
    
    if not resume_files:
        print(f"No resume files found in the '{resume_dir}' directory.")
        return

    output_file = 'resume_details.csv'
    
    # Process each resume one at a time
    for file_path in resume_files:
        filename = os.path.basename(file_path)
        
        # Check if this file has already been processed
        if check_if_processed(filename, output_file):
            print(f"Skipping {filename} - already processed")
            continue
        
        print(f"\nProcessing: {filename}")
        parsed_info = process_single_resume(file_path)
        if parsed_info:
            # response = input("Press Enter to process the next resume (or 'q' to quit)...")
            # if response.lower() == 'q':
            #     print("Stopping resume processing.")
            #     break
            print(f"Successfully processed {filename}")

if __name__ == "__main__":
    main()
