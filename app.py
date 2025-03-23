from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from Dhan_Tradehull import Tradehull
import asyncio
import json
from typing import Dict, List
import time
from datetime import datetime

app = FastAPI(title="NIFTY 50 Stock Tracker API")

# Add CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dhan API credentials - replace with your actual credentials
CLIENT_CODE = "1106534888"
TOKEN_ID = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzQ0MTcwODIxLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNjUzNDg4OCJ9.bU3NSe4Lsc4L3IyB8b_5XLMIIT2edgPr8SCPUJDGs-T9fjpeCWWc_5dmMrtxzQvOXveEawbJVduKOR4-3uPlJw"




# NIFTY 50 stocks list
NIFTY50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC", "SBIN", 
    "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI", 
    "TITAN", "SUNPHARMA", "HCLTECH", "ULTRACEMCO", "ADANIPORTS", "WIPRO", "BAJAJFINSV", 
    "NESTLEIND", "TATAMOTORS", "NTPC", "POWERGRID", "JSWSTEEL", "TATASTEEL", "M&M", 
    "TECHM", "DRREDDY", "INDUSINDBK", "ADANIENT", "GRASIM", "SBILIFE", "DIVISLAB", 
    "APOLLOHOSP", "ONGC", "HINDALCO", "COALINDIA", "CIPLA", "EICHERMOT", "BRITANNIA", 
    "BAJAJ-AUTO", "TATACONSUM", "LTIM", "UPL", "BPCL", "HEROMOTOCO", "HDFCLIFE"
]

# Global storage for stock data
stock_data = {}
last_updated = None
last_market_status = "Unknown"

# Initialize Dhan Tradehull client
tradehull_client = Tradehull(CLIENT_CODE, TOKEN_ID)

def format_stock_data(ltp_data, historical_data=None):
    """Format stock data with additional information if available"""
    formatted_data = []
    
    for symbol, price in ltp_data.items():
        stock_info = {
            "symbol": symbol,
            "name": get_company_name(symbol),  # Helper function to map symbols to names
            "price": price,
            "change": 0,  # Default value
            "changePercent": 0,  # Default value
            "volume": "N/A",
            "dayHigh": price,  # Default to current price if we don't have historical data
            "dayLow": price,   # Default to current price if we don't have historical data
        }
        
        # If we have historical data for this stock, add change calculations
        if historical_data and symbol in historical_data:
            hist = historical_data[symbol]
            prev_close = hist.get("prevClose", price)
            
            # Calculate change and change percent
            change = price - prev_close
            change_percent = (change / prev_close * 100) if prev_close > 0 else 0
            
            stock_info.update({
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "dayHigh": hist.get("dayHigh", price),
                "dayLow": hist.get("dayLow", price),
                "volume": hist.get("volume", "N/A"),
            })
        
        formatted_data.append(stock_info)
    
    # Sort by symbol
    formatted_data.sort(key=lambda x: x["symbol"])
    return formatted_data

def get_company_name(symbol):
    """Map stock symbols to company names"""
    company_names = {
        "RELIANCE": "Reliance Industries Ltd.",
        "TCS": "Tata Consultancy Services Ltd.",
        "HDFCBANK": "HDFC Bank Ltd.",
        "ICICIBANK": "ICICI Bank Ltd.",
        "INFY": "Infosys Ltd.",
        "HINDUNILVR": "Hindustan Unilever Ltd.",
        "ITC": "ITC Ltd.",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel Ltd.",
        "KOTAKBANK": "Kotak Mahindra Bank Ltd.",
        "LT": "Larsen & Toubro Ltd.",
        "AXISBANK": "Axis Bank Ltd.",
        "BAJFINANCE": "Bajaj Finance Ltd.",
        "ASIANPAINT": "Asian Paints Ltd.",
        "MARUTI": "Maruti Suzuki India Ltd.",
        "TITAN": "Titan Company Ltd.",
        "SUNPHARMA": "Sun Pharmaceutical Industries Ltd.",
        "HCLTECH": "HCL Technologies Ltd.",
        "ULTRACEMCO": "UltraTech Cement Ltd.",
        "ADANIPORTS": "Adani Ports and Special Economic Zone Ltd.",
        "WIPRO": "Wipro Ltd.",
        "BAJAJFINSV": "Bajaj Finserv Ltd.",
        "NESTLEIND": "Nestle India Ltd.",
        "TATAMOTORS": "Tata Motors Ltd.",
        "NTPC": "NTPC Ltd.",
        "POWERGRID": "Power Grid Corporation of India Ltd.",
        "JSWSTEEL": "JSW Steel Ltd.",
        "TATASTEEL": "Tata Steel Ltd.",
        "M&M": "Mahindra & Mahindra Ltd.",
        "TECHM": "Tech Mahindra Ltd.",
        "DRREDDY": "Dr. Reddy's Laboratories Ltd.",
        "INDUSINDBK": "IndusInd Bank Ltd.",
        "ADANIENT": "Adani Enterprises Ltd.",
        "GRASIM": "Grasim Industries Ltd.",
        "SBILIFE": "SBI Life Insurance Company Ltd.",
        "DIVISLAB": "Divi's Laboratories Ltd.",
        "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd.",
        "ONGC": "Oil and Natural Gas Corporation Ltd.",
        "HINDALCO": "Hindalco Industries Ltd.",
        "COALINDIA": "Coal India Ltd.",
        "CIPLA": "Cipla Ltd.",
        "EICHERMOT": "Eicher Motors Ltd.",
        "BRITANNIA": "Britannia Industries Ltd.",
        "BAJAJ-AUTO": "Bajaj Auto Ltd.",
        "TATACONSUM": "Tata Consumer Products Ltd.",
        "LTIM": "L&T Infotech Ltd.",
        "UPL": "UPL Ltd.",
        "BPCL": "Bharat Petroleum Corporation Ltd.",
        "HEROMOTOCO": "Hero MotoCorp Ltd.",
        "HDFCLIFE": "HDFC Life Insurance Company Ltd."
    }
    return company_names.get(symbol, symbol)

async def update_stock_data():
    """Function to update stock data periodically"""
    global stock_data, last_updated, last_market_status
    
    while True:
        try:
            # Check if market is open
            current_time = datetime.now().time()
            
            # Define market hours (9:15 AM to 3:30 PM IST on weekdays)
            market_open = current_time >= datetime.strptime("09:15:00", "%H:%M:%S").time()
            market_close = current_time <= datetime.strptime("15:30:00", "%H:%M:%S").time()
            is_weekday = datetime.now().weekday() < 5  # Monday-Friday are 0-4
            
            if is_weekday and market_open and market_close:
                market_status = "Open"
            else:
                market_status = "Closed"
            
            # Update status only if it changed
            if market_status != last_market_status:
                print(f"Market is now {market_status}")
                last_market_status = market_status
            
            # Always fetch data even if market is closed (for testing and to show last available prices)
            try:
                # Get LTP data for all NIFTY 50 stocks
                ltp_data = tradehull_client.get_ltp_data(names=NIFTY50_STOCKS)
                
                # Update global data store
                stock_data = format_stock_data(ltp_data)
                last_updated = datetime.now()
                
                print(f"Updated prices for {len(ltp_data)} stocks at {last_updated}")
            except Exception as e:
                print(f"Error fetching stock data: {str(e)}")
        
        except Exception as e:
            print(f"Error in update loop: {str(e)}")
        
        # Wait before updating again (5 seconds during market hours, 60 seconds when closed)
        await asyncio.sleep(5 if market_status == "Open" else 60)

@app.on_event("startup")
async def startup_event():
    """Start the background task to update stock data"""
    asyncio.create_task(update_stock_data())

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NIFTY 50 Stock Tracker API",
        "endpoints": {
            "stocks": "/api/stocks",
            "stock": "/api/stock/{symbol}"
        }
    }

@app.get("/api/stocks")
async def get_stocks():
    """Get all NIFTY 50 stocks data"""
    if not stock_data:
        raise HTTPException(status_code=503, detail="Stock data not yet available")
    
    return {
        "data": stock_data,
        "lastUpdated": last_updated.isoformat() if last_updated else None,
        "marketStatus": last_market_status
    }

@app.get("/api/stock/{symbol}")
async def get_stock(symbol: str):
    """Get data for a specific stock"""
    if not stock_data:
        raise HTTPException(status_code=503, detail="Stock data not yet available")
    
    # Find the requested stock
    for stock in stock_data:
        if stock["symbol"] == symbol.upper():
            return {
                "data": stock,
                "lastUpdated": last_updated.isoformat() if last_updated else None,
                "marketStatus": last_market_status
            }
    
    raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)