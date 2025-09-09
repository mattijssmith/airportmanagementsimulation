# Airport Simulation (Streamlit)

## Local
1. `pip install -r requirements.txt`
2. Create `config.yaml` from `config.example.yaml`:
   - Put bcrypt hash (not plain text)
   - Use a 32–64 char random cookie key
3. `streamlit run streamlit_app.py`

## Deploy on Streamlit Community Cloud
- Link this repo
- Select `streamlit_app.py` as the main file
- Add secrets (see below)
