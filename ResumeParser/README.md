# Resume Parser

A Python application that extracts information from resumes (PDF, DOCX, and TXT formats) using OpenAI's GPT model and saves the extracted information to a CSV file.

## Features

- Supports multiple file formats: PDF, DOCX, and TXT
- Uses OpenAI's GPT model for accurate information extraction
- Extracts:
  - Full Name
  - Contact Information (Email and Phone)
  - Skills
  - Work Experience (with job titles, companies, and dates)
- Saves results to a CSV file
- Avoids duplicate processing of resumes

## Requirements

- Windows operating system
- PowerShell
- Internet connection (for Python installation and OpenAI API)
- OpenAI API key

## Quick Setup

1. Clone or download this repository
2. Open PowerShell as Administrator
3. Navigate to the project directory
4. Run the setup script:
```powershell
.\setup.ps1
```

The setup script will:
- Check and install Python 3.12.4 if not present
- Create and activate a virtual environment
- Install required dependencies
- Set up the OpenAI API key
- Create the resumes directory

## Manual Setup

If you prefer to set up manually:

1. Install Python 3.12.4
2. Create and activate a virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate
```

3. Install dependencies:
```powershell
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

5. Create a 'resumes' directory and place your resume files in it

## Usage

1. Place your resume files (PDF, DOCX, or TXT) in the 'resumes' directory
2. Run the parser:
```powershell
python resume_parser.py
```

The parsed information will be saved in `resume_details.csv`

## Notes

- The parser uses OpenAI's GPT model for accurate information extraction
- Each resume is processed only once to avoid duplicates
- The CSV file includes: filename, name, email, phone, skills, and experience
- For best results, ensure resumes are properly formatted and readable
