#!/bin/bash

# This script activates the virtual environment and then executes all
# Jupyter notebooks in the correct order to validate them.

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found!"
    echo "Run ./setup.sh first to install dependencies"
    exit 1
fi

# Add the 'lib' directory to the PYTHONPATH for this script's execution.
# This allows the notebooks to import the custom modules without being modified.
export PYTHONPATH="${PWD}/lib:${PYTHONPATH:-}"
echo "Temporarily added './lib' to PYTHONPATH."
echo "---"

# Define the exact order to run the notebooks for a valid workflow.
NOTEBOOKS_ORDERED=(
  "00_Setup_and_Installation.ipynb"
  "01_Quality_Assessment_Agent.ipynb"
  "02_Metadata_Enrichment_Agent.ipynb"
  "03_Discovery_Agent.ipynb"
  "04_LLM_Enrichment.ipynb"
  "05_Generate_Curation_Report.ipynb"
)

echo "Will execute notebooks in this order:"
for nb in "${NOTEBOOKS_ORDERED[@]}"; do
  echo "  - $nb"
done
echo "---"

# Loop through each notebook and execute it.
for notebook in "${NOTEBOOKS_ORDERED[@]}"
do
  if [ ! -f "$notebook" ]; then
    echo "⚠️  Warning: Notebook not found, skipping: $notebook"
    continue
  fi

  echo "▶️  Executing: $notebook"

  # Execute the notebook in place, overwriting it with the output.
  # The --log-level=ERROR flag will hide verbose output unless there is a failure.
  jupyter nbconvert --to notebook --execute --inplace --log-level=ERROR "$notebook"

  # Check the exit code of the last command.
  if [ $? -eq 0 ]; then
    echo "✅ Success: $notebook completed without errors."
  else
    echo "❌ Error: $notebook failed to execute. The notebook has been updated with the error details."
    exit 1 # Exit the script if any notebook fails.
  fi
  echo "---"
done

echo "🎉 All notebooks executed successfully!"
