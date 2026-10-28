import yfinance as yf
import pandas as pd

def fetch_eod_data(tickers, period="1mo"):
    data = {}
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if not hist.empty:
            data[ticker] = hist
    return data

def detect_volume_spike(df, threshold=2.0):
    if len(df) < 2:
        return False, 0.0, 0.0
    recent_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].iloc[:-1].mean()
    if recent_vol > (threshold * avg_vol):
        return True, recent_vol, avg_vol
    return False, recent_vol, avg_vol

def detect_price_movement(df, threshold_pct=5.0):
    if len(df) < 2:
        return False, 0.0
    recent_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    pct_change = ((recent_close - prev_close) / prev_close) * 100
    if abs(pct_change) >= threshold_pct:
        return True, pct_change
    return False, pct_change


import requests

def fetch_nse_announcements(symbol):
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []
    
    
import os
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def fetch_company_fundamentals(ticker_symbol):
    url = f"https://www.screener.in/company/{ticker_symbol}/consolidated/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    response = requests.get(url, headers=headers)
    data = {"about": "", "ratios": {}}
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        about_section = soup.find('div', class_='company-profile')
        if about_section:
            data["about"] = about_section.text.strip()
            
        ratios_list = soup.find('ul', id='top-ratios')
        if ratios_list:
            for li in ratios_list.find_all('li'):
                name = li.find('span', class_='name')
                value = li.find('span', class_='number')
                if name and value:
                    data["ratios"][name.text.strip()] = value.text.strip()
    return data

def process_push_digest(announcement_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Categorize this corporate filing into one of the reference categories (e.g., results, management_change, M&A).
    Provide a concise one-line summary. 
    If it is a management_change, extract the person's name and previous role.
    Filing: {announcement_text}
    """
    response = model.generate_content(prompt)
    return response.text

def process_pull_analysis(transcript_text, financial_data, analysis_type):
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = f"""
    Act as a financial analyst. Generate a {analysis_type} view strictly using the following primary sources. 
    Do not use secondary knowledge or broker notes.
    Transcript: {transcript_text}
    Financials: {financial_data}
    """
    response = model.generate_content(prompt)
    return response.text