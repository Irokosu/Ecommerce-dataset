# E-commerce Intelligence Dashboard

An interactive Streamlit portfolio project for exploring e-commerce sales, customer behaviour, product performance, market performance, and cancellation risk.

## Live Dashboard

Add the deployed Streamlit URL here after publishing:

`[Open the live dashboard](YOUR_STREAMLIT_APP_URL)`

## Project Highlights

- Completed-sales revenue and order trend analysis
- Interactive country and market performance comparison
- Product ranking by revenue, units sold, orders, and customer reach
- Repeat-purchase and customer-value exploration
- Cancellation and return monitoring
- Date and country filters
- Downloadable filtered completed-sales data
- Exploratory analysis documented in `Influx_analysis.ipynb`

## Dashboard Preview

Add a screenshot or GIF here after deployment:

`![Dashboard preview](assets/dashboard-preview.png)`

## Dataset

The project uses the Online Retail transaction data supplied in `data/influx_ecommerce.csv`. Each record represents a transaction line with invoice, product, quantity, price, customer, country, and timestamp fields.

Revenue is calculated as:

`Quantity × UnitPrice`

The dashboard distinguishes between:

- **Completed sales:** non-cancelled invoices with positive quantities
- **Returns or cancellations:** negative-quantity transaction lines

The dataset does not contain stock-on-hand, supplier lead time, profit margin, or acquisition-cost fields. Inventory conclusions are therefore based on historical sales velocity and should not be interpreted as direct stock-level measurements.

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Streamlit

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`.

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select **New app**.
4. Choose the GitHub repository and branch.
5. Set the main file to `app.py`.
6. Deploy.

The repository must contain `app.py`, `requirements.txt`, and `data/influx_ecommerce.csv`.

## Repository Structure

```text
.
├── app.py
├── Influx_analysis.ipynb
├── README.md
├── requirements.txt
├── .gitignore
└── data/
    └── influx_ecommerce.csv
```

## Notebook and Dashboard Roles

The notebook is the exploratory analysis record. It contains data cleaning, investigation, visualisation, and written findings.

The Streamlit app is the presentation layer. It recreates the important metrics interactively so recruiters can explore the project without running the notebook.

The notebook does not need to be refactored into a Python file before deployment. A separate `.py` file is appropriate for the dashboard because Streamlit runs Python scripts, while the notebook remains useful as supporting documentation.

## Portfolio Notes

For a stronger portfolio presentation, add:

- A dashboard screenshot
- A short project walkthrough in the repository description
- The deployed Streamlit URL
- A concise list of business recommendations
- A note explaining the limitations of transaction-only inventory analysis
