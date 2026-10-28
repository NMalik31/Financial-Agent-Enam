import streamlit as st
import pandas as pd
from backend import (
    fetch_eod_data, 
    detect_volume_spike, 
    detect_price_movement, 
    fetch_nse_announcements, 
    fetch_company_fundamentals, 
    process_push_digest, 
    process_pull_analysis
)

st.set_page_config(page_title="FINN - Investment Agent", layout="centered", initial_sidebar_state="collapsed")

st.title("FINN: Financial Investment Agent")

mode = st.radio("Interaction Mode", ["Push (Alerts & Digest)", "Pull (On-Demand Research)"], horizontal=True)

if mode == "Push (Alerts & Digest)":
    st.header("Daily Digest & Alerts")
    
    portfolio_input = st.text_input("Portfolio Tickers (comma-separated, with .NS)", value="RELIANCE.NS, TCS.NS")
    tickers = [t.strip() for t in portfolio_input.split(",")]
    
    if st.button("Refresh Feed"):
        with st.spinner("Scanning market data and filings..."):
            st.subheader("Triggered Alerts")
            eod_data = fetch_eod_data(tickers, period="5d")
            
            alerts_found = False
            for ticker, df in eod_data.items():
                vol_spike, recent_vol, avg_vol = detect_volume_spike(df)
                if vol_spike:
                    alerts_found = True
                    st.error(f"**{ticker}**: Unusual volume detected ({recent_vol:,.0f} vs avg {avg_vol:,.0f})")
                    
                price_spike, pct_change = detect_price_movement(df)
                if price_spike:
                    alerts_found = True
                    st.warning(f"**{ticker}**: Significant price movement of {pct_change:.2f}%")
            
            if not alerts_found:
                st.success("No unusual market movements detected today.")
                
            st.markdown("---")
            st.subheader("24-Hour Windowed Digest")
            
            for ticker in tickers:
                base_ticker = ticker.replace(".NS", "").replace(".BO", "")
                st.markdown(f"**{base_ticker}**")
                
                # Fetch announcements
                announcements = fetch_nse_announcements(base_ticker)
                
                # Process the latest 2 announcements to avoid rate limits/long load times in demo
                if not announcements or len(announcements) == 0:
                    st.info("No recent filings found.")
                else:
                    try:
                        # Extract the data list if the API returns a dictionary, else assume it's a list
                        data_list = announcements.get('data', []) if isinstance(announcements, dict) else announcements
                        
                        for ann in data_list[:2]:
                            desc = ann.get('desc', 'Corporate Filing')
                            digest_result = process_push_digest(desc)
                            st.write(f"- {digest_result}")
                    except Exception as e:
                        st.info(f"Could not parse filings for {base_ticker}. (Check API/Network)")

elif mode == "Pull (On-Demand Research)":
    st.header("On-Demand Research")
    
    ticker_input = st.text_input("Enter Ticker Symbol (e.g., RELIANCE)", value="RELIANCE")
    analysis_type = st.selectbox(
        "Select View", 
        [
            "Business snapshot", 
            "Financial snapshot", 
            "Trajectory", 
            "Balance sheet", 
            "Cash quality", 
            "Narrative vs. numbers", 
            "Guidance", 
            "Bull vs. bear"
        ]
    )
    
    if st.button("Generate Analysis"):
        base_ticker = ticker_input.replace(".NS", "").replace(".BO", "")
        with st.spinner(f"Pulling primary sources and analyzing {base_ticker}..."):
            
            # Fetch fundamentals from Screener.in
            fundamentals = fetch_company_fundamentals(base_ticker)
            
            if not fundamentals.get("about") and not fundamentals.get("ratios"):
                st.error("Could not fetch fundamental data. Please check the ticker symbol.")
            else:
                # Mocking a recent transcript excerpt for the prototype since full PDF parsing requires OCR/PyPDF2
                mock_transcript = f"Management Commentary for {base_ticker}: We expect to maintain our growth momentum. Margins might face slight pressure due to raw material costs, but we are guiding for a 12-15% revenue growth next year with a strong focus on cash conversion."
                
                analysis_result = process_pull_analysis(
                    transcript_text=mock_transcript,
                    financial_data=str(fundamentals),
                    analysis_type=analysis_type
                )
                
                st.markdown(f"### {analysis_type}")
                st.write(analysis_result)
                
                with st.expander("View Raw Fundamental Data"):
                    st.json(fundamentals)