# Check if Python 3.12.4 is installed
$pythonVersion = "3.12.4"
$pythonInstaller = "python-3.12.4-amd64.exe"
$pythonUrl = "https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe"

Write-Host "Checking for Python $pythonVersion..."

try {
    $installedVersion = python --version 2>&1
    if ($installedVersion -like "*Python $pythonVersion*") {
        Write-Host "Python $pythonVersion is already installed."
    } else {
        Write-Host "Installing Python $pythonVersion..."
        
        # Download Python installer
        Write-Host "Downloading Python installer..."
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
        
        # Install Python with required options
        Write-Host "Installing Python..."
        Start-Process -FilePath ".\$pythonInstaller" -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
        
        # Clean up installer
        Remove-Item -Path ".\$pythonInstaller"
        
        Write-Host "Python $pythonVersion installed successfully."
    }
} catch {
    Write-Host "Error checking/installing Python: $_"
    exit 1
}

# Create and activate virtual environment
Write-Host "Setting up virtual environment..."
if (-not (Test-Path "venv")) {
    python -m venv venv
}

# Activate virtual environment
.\venv\Scripts\Activate

# Install requirements
Write-Host "Installing requirements..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists, create if not
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..."
    Write-Host "Please enter your OpenAI API Key:"
    $apiKey = Read-Host
    "OPENAI_API_KEY=$apiKey" | Out-File -FilePath ".env" -Encoding utf8
}

# Create resumes directory if it doesn't exist
if (-not (Test-Path "resumes")) {
    Write-Host "Creating resumes directory..."
    New-Item -ItemType Directory -Path "resumes"
    Write-Host "Please place your resume files in the 'resumes' directory."
}

Write-Host "`nSetup complete! You can now run the resume parser by executing:"
Write-Host "python resume_parser.py"

# Ask if user wants to run the parser now
$runNow = Read-Host "Would you like to run the resume parser now? (y/n)"
if ($runNow -eq "y") {
    python resume_parser.py
}
