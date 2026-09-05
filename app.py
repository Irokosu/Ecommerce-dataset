from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="E-commerce Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


DATA_PATH = Path(__file__).parent / "data" / "influx_ecommerce.csv"


@st.cache_data

def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, encoding="cp1252")
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"], errors="coerce")
    data["CustomerID"] = data["CustomerID"].astype(str).str.replace(r"\.0$", "", regex=True)
    data["InvoiceNo"] = data["InvoiceNo"].astype(str)
    data["TotalRevenue"] = data["Quantity"] * data["UnitPrice"]
    data["YearMonth"] = data["InvoiceDate"].dt.to_period("M").astype(str)
    data["IsCancelledInvoice"] = data["InvoiceNo"].str.startswith("C")
    data["IsReturn"] = data["Quantity"] < 0
    data["IsCompletedSale"] = (~data["IsCancelledInvoice"]) & (data["Quantity"] > 0)
    return data.dropna(subset=["InvoiceDate", "CustomerID", "Country"])


@st.cache_data

def build_completed_sales(data: pd.DataFrame) -> pd.DataFrame:
    return data[data["IsCompletedSale"]].copy()


def money(value: float) -> str:
    return f"${value:,.0f}"


def product_table(sales: pd.DataFrame) -> pd.DataFrame:
    return (
        sales.groupby("StockCode", as_index=False)
        .agg(
            Description=("Description", "first"),
            Units_Sold=("Quantity", "sum"),
            Revenue=("TotalRevenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
        )
        .sort_values("Revenue", ascending=False)
    )


def country_table(sales: pd.DataFrame) -> pd.DataFrame:
    result = (
        sales.groupby("Country", as_index=False)
        .agg(
            Revenue=("TotalRevenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            Units_Sold=("Quantity", "sum"),
        )
    )
    result["AOV"] = result["Revenue"] / result["Orders"]
    result["Revenue_Per_Customer"] = result["Revenue"] / result["Customers"]
    return result.sort_values("Revenue", ascending=False)


def customer_table(sales: pd.DataFrame) -> pd.DataFrame:
    result = (
        sales.groupby("CustomerID", as_index=False)
        .agg(
            Revenue=("TotalRevenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Units_Sold=("Quantity", "sum"),
            First_Purchase=("InvoiceDate", "min"),
            Last_Purchase=("InvoiceDate", "max"),
        )
    )
    result["AOV"] = result["Revenue"] / result["Orders"]
    result["Customer_Type"] = result["Orders"].map(
        lambda orders: "Repeat Customer" if orders > 1 else "One-Time Customer"
    )
    return result.sort_values("Revenue", ascending=False)


try:
    raw = load_data(DATA_PATH)
except FileNotFoundError:
    st.error("The source file was not found at data/influx_ecommerce.csv.")
    st.stop()

sales = build_completed_sales(raw)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetricValue"] {font-size: 1.7rem;}
    .dashboard-subtitle {color: #64748b; font-size: 1.05rem; margin-top: -0.7rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("E-commerce Intelligence Dashboard")
st.markdown(
    "<p class='dashboard-subtitle'>A decision-focused view of sales, customers, products, markets, and operational risk.</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Dashboard Filters")
    min_date = sales["InvoiceDate"].min().date()
    max_date = sales["InvoiceDate"].max().date()
    date_range = st.date_input(
        "Transaction date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    start_date, end_date = min_date, max_date
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_sales = sales[
            sales["InvoiceDate"].dt.date.between(start_date, end_date)
        ].copy()
    else:
        filtered_sales = sales.copy()

    countries = sorted(filtered_sales["Country"].unique())
    selected_countries = st.multiselect(
        "Countries",
        options=countries,
        default=[],
        placeholder="All countries",
    )
    if selected_countries:
        filtered_sales = filtered_sales[
            filtered_sales["Country"].isin(selected_countries)
        ].copy()

    st.caption(
        "Completed sales exclude cancelled invoices and negative-quantity transactions."
    )

if filtered_sales.empty:
    st.warning("No completed sales match the selected filters.")
    st.stop()

products = product_table(filtered_sales)
countries = country_table(filtered_sales)
customers = customer_table(filtered_sales)
returns = raw[raw["IsReturn"]].copy()
returns = returns[
    returns["InvoiceDate"].dt.date.between(start_date, end_date)
].copy()
if selected_countries:
    returns = returns[returns["Country"].isin(selected_countries)].copy()

monthly = (
    filtered_sales.assign(Month=filtered_sales["InvoiceDate"].dt.to_period("M").astype(str))
    .groupby("Month", as_index=False)
    .agg(Revenue=("TotalRevenue", "sum"), Orders=("InvoiceNo", "nunique"), Units=("Quantity", "sum"))
)
monthly["AOV"] = monthly["Revenue"] / monthly["Orders"]

repeat_rate = (customers["Orders"] > 1).mean() * 100
return_rate = returns["Quantity"].abs().sum() / filtered_sales["Quantity"].sum() * 100

kpi_columns = st.columns(5)
kpi_columns[0].metric("Completed revenue", money(filtered_sales["TotalRevenue"].sum()))
kpi_columns[1].metric("Orders", f"{filtered_sales['InvoiceNo'].nunique():,}")
kpi_columns[2].metric("Customers", f"{filtered_sales['CustomerID'].nunique():,}")
kpi_columns[3].metric("Average order value", money(filtered_sales.groupby("InvoiceNo")["TotalRevenue"].sum().mean()))
kpi_columns[4].metric("Repeat-customer rate", f"{repeat_rate:.1f}%")

st.divider()

overview_tab, customers_tab, products_tab, markets_tab, operations_tab = st.tabs(
    ["Overview", "Customers", "Products", "Markets", "Operations"]
)

with overview_tab:
    st.subheader("Revenue trend")
    st.caption("Use the date and country filters in the sidebar to focus the view.")
    st.plotly_chart(
        px.line(
            monthly,
            x="Month",
            y="Revenue",
            markers=True,
            labels={"Revenue": "Revenue ($)", "Month": "Month"},
            template="plotly_white",
        ).update_layout(height=420),
        use_container_width=True,
    )
    left, right = st.columns(2)
    with left:
        st.subheader("Top products by revenue")
        st.plotly_chart(
            px.bar(
                products.head(10).sort_values("Revenue"),
                x="Revenue",
                y="Description",
                orientation="h",
                labels={"Revenue": "Revenue ($)", "Description": ""},
                template="plotly_white",
            ).update_layout(height=430),
            use_container_width=True,
        )
    with right:
        st.subheader("Revenue by country")
        st.plotly_chart(
            px.bar(
                countries.head(10).sort_values("Revenue"),
                x="Revenue",
                y="Country",
                orientation="h",
                labels={"Revenue": "Revenue ($)", "Country": ""},
                template="plotly_white",
            ).update_layout(height=430),
            use_container_width=True,
        )

with customers_tab:
    st.subheader("Customer value and repeat purchasing")
    left, right = st.columns(2)
    with left:
        segment_counts = customers["Customer_Type"].value_counts().rename_axis("Customer Type").reset_index(name="Customers")
        st.plotly_chart(
            px.bar(
                segment_counts,
                x="Customer Type",
                y="Customers",
                color="Customer Type",
                text_auto=True,
                template="plotly_white",
            ).update_layout(showlegend=False, height=360),
            use_container_width=True,
        )
    with right:
        st.plotly_chart(
            px.scatter(
                customers,
                x="Orders",
                y="Revenue",
                size="Units_Sold",
                hover_name="CustomerID",
                color="Customer_Type",
                log_y=True,
                labels={"Revenue": "Revenue ($)", "Orders": "Completed orders"},
                template="plotly_white",
            ).update_layout(height=360),
            use_container_width=True,
        )
    st.dataframe(
        customers.head(25).style.format({"Revenue": "${:,.2f}", "AOV": "${:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

with products_tab:
    st.subheader("Product performance")
    metric = st.selectbox("Rank products by", ["Revenue", "Units_Sold", "Orders", "Customers"])
    ranked_products = products.sort_values(metric, ascending=False).head(25)
    st.plotly_chart(
        px.bar(
            ranked_products.sort_values(metric),
            x=metric,
            y="Description",
            orientation="h",
            labels={metric: metric.replace("_", " "), "Description": ""},
            template="plotly_white",
        ).update_layout(height=650),
        use_container_width=True,
    )
    st.dataframe(
        ranked_products.style.format({"Revenue": "${:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

with markets_tab:
    st.subheader("Market performance")
    countries["Revenue Share"] = countries["Revenue"] / countries["Revenue"].sum() * 100
    st.plotly_chart(
        px.scatter(
            countries,
            x="Customers",
            y="Revenue",
            size="Orders",
            color="AOV",
            hover_name="Country",
            labels={"Revenue": "Revenue ($)", "AOV": "Average order value ($)"},
            color_continuous_scale="Tealgrn",
            template="plotly_white",
        ).update_layout(height=500),
        use_container_width=True,
    )
    st.dataframe(
        countries.style.format({
            "Revenue": "${:,.2f}",
            "AOV": "${:,.2f}",
            "Revenue_Per_Customer": "${:,.2f}",
            "Revenue Share": "{:.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

with operations_tab:
    st.subheader("Cancellations and returns")
    return_value = returns["Quantity"].abs().mul(returns["UnitPrice"]).sum()
    op_columns = st.columns(3)
    op_columns[0].metric("Returned/cancelled units", f"{returns['Quantity'].abs().sum():,.0f}")
    op_columns[1].metric("Gross value affected", money(return_value))
    op_columns[2].metric("Unit return rate", f"{return_rate:.2f}%")
    monthly_returns = (
        returns.assign(Month=returns["InvoiceDate"].dt.to_period("M").astype(str))
        .groupby("Month", as_index=False)
        .agg(Units=("Quantity", lambda values: values.abs().sum()), Value=("TotalRevenue", lambda values: values.abs().sum()))
    )
    st.plotly_chart(
        px.bar(
            monthly_returns,
            x="Month",
            y="Value",
            labels={"Value": "Gross value affected ($)"},
            color_discrete_sequence=["#d95f59"],
            template="plotly_white",
        ).update_layout(height=400),
        use_container_width=True,
    )

st.divider()

csv_data = filtered_sales.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered completed sales",
    data=csv_data,
    file_name="filtered_completed_sales.csv",
    mime="text/csv",
)

st.caption("Portfolio dashboard built from the Online Retail transaction dataset. Revenue is calculated as Quantity × UnitPrice.")
