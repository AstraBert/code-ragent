eval "$(conda shell.bash hook)"

conda activate code-ragent
cd /backend/
uvicorn api:app --host 0.0.0.0 --port 8000
conda deactivate
