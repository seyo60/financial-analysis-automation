import requests
from bs4 import BeautifulSoup
import re
from typing import Tuple, Optional

def fetch_hisse_lotlari(url: str = "https://borsa.doviz.com/halka-arz/dof-robotik-sanayi-as/194") -> Tuple[Optional[int], Optional[int]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Pay Lot'u bul
        pay_lot = None
        pay_div = soup.find("div", class_="text-xs text-blue-gray-2", string="Pay")
        if pay_div:
            pay_value_div = pay_div.find_next("div", class_="text-md font-semibold text-white mt-4")
            if pay_value_div:
                pay_text = pay_value_div.get_text(strip=True)
                pay_match = re.search(r'(\d{1,3}(?:\.\d{3})*)', pay_text)
                if pay_match:
                    pay_lot = int(pay_match.group(1).replace(".", ""))

        # Ek Pay Lot'u bul
        ek_pay_lot = None
        ek_pay_div = soup.find("div", class_="text-xs text-blue-gray-2", string="Ek Pay")
        if ek_pay_div:
            ek_pay_value_div = ek_pay_div.find_next("div", class_="text-md font-semibold text-white mt-4")
            if ek_pay_value_div:
                ek_pay_text = ek_pay_value_div.get_text(strip=True)
                ek_pay_match = re.search(r'(\d{1,3}(?:\.\d{3})*)', ek_pay_text)
                if ek_pay_match:
                    ek_pay_lot = int(ek_pay_match.group(1).replace(".", ""))

        return pay_lot, ek_pay_lot

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        return None, None