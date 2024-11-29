####################################################
# This is Dam Son Quy's Financial Programming Code #
####################################################

# Importing libaries
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import date
from plotly.subplots import make_subplots

st.sidebar.title("S&P 500 Stock Dashboard")

# Get S&P500 data
@st.cache_data
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)
    return table[0]['Symbol'].tolist()

tickers = get_sp500_tickers()
selected_ticker = st.sidebar.selectbox("Select a stock", tickers)

# Cache only the serializable parts of stock data
@st.cache_data
def get_serializable_stock_data(ticker):
    stock = yf.Ticker(ticker)
    history = stock.history(period="5y")
    history.index = history.index.tz_localize(None)  # Remove timezone to make datetime objects naive
    return {
        "info": stock.info,
        "history": history.reset_index(),
        "financials": {
            "Income Statement": {"Annual": stock.financials, "Quarterly": stock.quarterly_financials},
            "Balance Sheet": {"Annual": stock.balance_sheet, "Quarterly": stock.quarterly_balance_sheet},
            "Cash Flow": {"Annual": stock.cashflow, "Quarterly": stock.quarterly_cashflow}
        }
    }

# Use st.cache_resource for non-serializable objects
@st.cache_resource
def get_ticker_object(ticker):
    return yf.Ticker(ticker)

if "data" not in st.session_state:
    st.session_state["data"] = None

if st.sidebar.button("Update Data"):
    st.session_state["data"] = get_serializable_stock_data(selected_ticker)
    st.session_state["ticker"] = get_ticker_object(selected_ticker)

# Check if data is available before rendering tabs
if st.session_state["data"]:
    data = st.session_state["data"]
    stock = st.session_state["ticker"]

    # Tabs for the dashboard
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Chart", "Financials", "Monte Carlo Simulation", "Analysis"])

    # Tab 1: Summary
    with tab1:
        st.header(f"Summary of {selected_ticker}")
        info = data["info"]

        st.subheader("Company Profile")
        st.write(f"**Name:** {info.get('longName', 'N/A')}")
        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
        st.write(f"**Country:** {info.get('country', 'N/A')}")
        st.write(f"**Employees:** {info.get('fullTimeEmployees', 'N/A')}")

        st.subheader("Business Summary")
        st.markdown(info.get("longBusinessSummary", "No summary available."), unsafe_allow_html=True)

        st.subheader("Major Shareholders")
        shareholders = stock.major_holders
        st.write(shareholders if shareholders is not None else "No data available.")

        # Stock Chart Section
        st.subheader("Stock Price and Volume Chart")

        # Extract historical data
        stock_data = pd.DataFrame(data["history"])
        stock_data['Date'] = pd.to_datetime(stock_data['Date'])

        # Dropdown for selecting duration
        duration_options = {"1M": 30, "3M": 90, "6M": 180, "YTD": None, "1Y": 365, "3Y": 1095, "5Y": 1825, "MAX": None}
        selected_duration = st.selectbox("Select Duration", duration_options.keys())

        # Calculate start date based on duration
        if selected_duration == "YTD":
            start_date = date(date.today().year, 1, 1)
        elif duration_options[selected_duration] is not None:
            start_date = date.today() - pd.Timedelta(days=duration_options[selected_duration])
        else:
            start_date = stock_data['Date'].min()  # MAX option

        # Filter data
        filtered_data = stock_data[stock_data['Date'] >= pd.Timestamp(start_date)]

        # Create the figure
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add area plot for stock price
        fig.add_trace(
            go.Scatter(
                x=filtered_data['Date'],
                y=filtered_data['Close'],
                mode='lines',
                fill='tozeroy',
                fillcolor='rgba(0, 128, 255, 0.2)',
                name="Stock Price",
                line=dict(color='green'),
            ),
            secondary_y=True,
        )

        # Add bar plot for volume
        fig.add_trace(
            go.Bar(
                x=filtered_data['Date'],
                y=filtered_data['Volume'],
                name="Volume",
                marker_color='rgba(128, 128, 128, 0.5)',
            ),
            secondary_y=False,
        )

        # Add time range buttons
        fig.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=3, label="3Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX"),
                ])
            ),
            rangeslider_visible=True,
        )

        # Customize layout
        fig.update_layout(
            title=f"Stock Price and Volume of {selected_ticker}",
            xaxis_title="Date",
            yaxis_title="Price (USD)",
            yaxis2_title="Volume",
            template="plotly_white",
            showlegend=False,
            height=500,
        )

        st.plotly_chart(fig)

    # Tab 2: Chart
    with tab2:
        st.header("Stock Price Chart")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date(2020, 1, 1))
        with col2:
            end_date = st.date_input("End Date", value=date.today())

        # Filter data based on the selected date range
        stock_data = pd.DataFrame(data["history"])
        stock_data['Date'] = pd.to_datetime(stock_data['Date'])
        filtered_data = stock_data[(stock_data['Date'] >= pd.Timestamp(start_date)) & (stock_data['Date'] <= pd.Timestamp(end_date))]

        # Create the figure with stock price and volume
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add stock price area plot
        area_plot = go.Scatter(
            x=filtered_data['Date'],
            y=filtered_data['Close'],
            fill='tozeroy',
            fillcolor='rgba(133, 133, 241, 0.2)',
            name="Stock Price",
            showlegend=False
        )
        fig.add_trace(area_plot, secondary_y=True)

        # Add volume bar plot with red/green colors based on price change
        bar_plot = go.Bar(
            x=filtered_data['Date'],
            y=filtered_data['Volume'],
            marker_color=np.where(filtered_data['Close'].pct_change() < 0, 'red', 'green'),
            name="Volume",
            showlegend=False
        )
        fig.add_trace(bar_plot, secondary_y=False)

        # Configure range selector buttons
        fig.update_xaxes(
            rangeslider_visible=False,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )

        # Customize layout
        fig.update_layout(template='plotly_white', title="Stock Price and Volume")
        fig.update_yaxes(title_text="Volume", range=[0, max(filtered_data['Volume'] * 1.2)], secondary_y=False)
        fig.update_yaxes(title_text="Stock Price", secondary_y=True)

        # Render the Plotly chart
        st.plotly_chart(fig)

    # Tab 3: Financials
    with tab3:
        st.header("Financial Information")
        financial_type = st.selectbox("Select Financial Statement", ["Income Statement", "Balance Sheet", "Cash Flow"])
        period = st.radio("Select Period", ["Annual", "Quarterly"])
        financial_data = data["financials"][financial_type][period]
        st.write(financial_data if not financial_data.empty else "No data available.")

    # Tab 4: Monte Carlo Simulation
    with tab4:
        st.header("Monte Carlo Simulation")
        num_simulations = st.selectbox("Number of Simulations", [200, 500, 1000])
        time_horizon = st.selectbox("Time Horizon (Days)", [30, 60, 90])
        returns = filtered_data['Close'].pct_change().dropna()
        last_price = filtered_data['Close'].iloc[-1]

        simulations = np.zeros((time_horizon, num_simulations))
        for i in range(num_simulations):
            prices = [last_price]
            for _ in range(time_horizon - 1):
                prices.append(prices[-1] * (1 + np.random.choice(returns)))
            simulations[:, i] = prices

        fig = go.Figure()
        for i in range(num_simulations):
            fig.add_trace(go.Scatter(x=list(range(time_horizon)), y=simulations[:, i], mode='lines', showlegend=False))
        st.plotly_chart(fig)

    # Tab 5: Analysis
    with tab5:
        st.header("Top 10 Companies with Largest Market Cap Increase")

        # Fetch the S&P 500 industry data
        sp500_data = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        available_industries = sp500_data['GICS Sector'].unique()

        # Dropdown to select industry
        selected_industry = st.selectbox("Select an Industry", available_industries)

        # Filter tickers by the selected industry
        industry_tickers = sp500_data[sp500_data['GICS Sector'] == selected_industry]['Symbol'].tolist()

        # Date range options for analysis
        date_options = {"1 Day": 1, "30 Days": 30, "90 Days": 90, "180 Days": 180, "365 Days": 365}
        selected_period = st.selectbox("Select Period", date_options.keys())

        # Spinner for processing feedback
        with st.spinner("Analyzing data, please wait..."):
            period_days = date_options[selected_period]
            results = []

            for ticker in industry_tickers:
                try:
                    # Fetch stock data for the ticker
                    ticker_data = yf.Ticker(ticker)
                    history = ticker_data.history(period="1y")
                    shares_outstanding = ticker_data.info.get("sharesOutstanding", None)

                    # Skip if shares outstanding or price history is not available
                    if shares_outstanding is None or history.empty:
                        continue

                    # Calculate the market cap change for the period
                    if len(history) > period_days:
                        start_price = history['Close'].iloc[-period_days]
                        end_price = history['Close'].iloc[-1]
                        market_cap_change = (end_price * shares_outstanding) - (start_price * shares_outstanding)

                        results.append({"Ticker": ticker, "Market Cap Change": market_cap_change})
                except Exception as e:
                    # Log and skip problematic tickers
                    continue

            # Convert results to a DataFrame and sort by market cap change
            if results:
                top_companies = pd.DataFrame(results).sort_values(by="Market Cap Change", ascending=False).head(10)

                # Display the results
                st.subheader(f"Top 10 Companies in {selected_industry} by Market Cap Increase ({selected_period})")
                st.write(top_companies)

                # Optional: Visualize the results as a bar chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=top_companies['Ticker'],
                    y=top_companies['Market Cap Change'],
                    marker_color='black'
                ))
                fig.update_layout(
                    title="Top 10 Companies by Market Cap Increase",
                    xaxis_title="Ticker",
                    yaxis_title="Market Cap Change",
                    template="plotly_white"
                )
                st.plotly_chart(fig)
            else:
                st.write("No data available for the selected industry and period.")