import streamlit as st
import numpy as np
import re
import tempfile
import fpdf
import yfinance as yf
from modules.data_extractor import extract_tables_from_docx
from modules.webScrapping import fetch_hisse_lotlari
from modules.ratio_calculator import (
    fk_orani, 
    fd_divide_favok as fddividefavok, 
    pd_divide_dd as pd_divided_dd,     
    borctoplamvarlik, 
    asittestorani,
    carioran,
    netkarmarji, 
    aktifkarlilik, 
    ozsermayekarliligi, 
    alacakdevirhizi, 
    stokdevirhizi
)
from modules.dcf_model import nwcdegisim, capex, vergiorani, fcf, bes_yillik_fcf, bes_yillik_indirgeme, terminal_degeri
from modules.visualization import draw_valuation_multiples_chart, draw_fcf_chart, draw_dcf_chart, draw_terminal_value_chart, draw_liquidity_chart, draw_debt_chart, draw_profitability_chart, draw_activity_chart, draw_financial_metrics_chart, create_pdf_report


st.set_page_config(page_title="Finansal Analiz", layout="wide")

def format_number(value, decimal_places=2):
    """Sayıyı binlik ayraçlarıyla formatlar"""
    try:
        if isinstance(value, (int, float)):
            return "{:,.{}f}".format(value, decimal_places).replace(",", "X").replace(".", ",").replace("X", ".")
        return value
    except:
        return value


def get_hisse_lotlari():
    try:
        lot_data = fetch_hisse_lotlari()
        
        if isinstance(lot_data, (tuple, list)):
            pay = lot_data[0] if len(lot_data) > 0 else 0
            ek_pay = lot_data[1] if len(lot_data) > 1 else 0
            return pay, ek_pay
        elif isinstance(lot_data, dict):
            pay = lot_data.get('pay_lot', 0)
            ek_pay = lot_data.get('ek_pay_lot', 0)
            return pay, ek_pay
        return 0, 0
        
    except Exception as e:
        st.error(f"Hata: {str(e)}")
        return 0, 0

def clean_numeric(value):
    """Binlik ayraçlı ve parantezli değerleri float'a çevirir"""
    if isinstance(value, str):
        value = value.strip()
        if value.startswith('(') and value.endswith(')'):
            value = '-' + value[1:-1]  
        value = value.replace('.', '').replace(',', '.')  
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


st.title("📊 Finansal Analiz Otomasyonu")

uploaded_file = st.file_uploader("Word dosyasını yükleyin (.docx)", type=["docx"])

kisaVadeli = 0.0
uzun_vadeli_borclanma_kisa_vadeli = 0.0
uzunVadeliBorc = 0.0
nakitVb = 0.0
finansalYatirimlar = 0.0
netKar = 0.0
finansmanGiderleri = 0.0
finansmanGelirleri = 0.0
amortismanVeItfaPaylari = 0.0
ozSermaye = 0.0

if uploaded_file:
    try:
        tables = extract_tables_from_docx(uploaded_file)
        if not tables:
            st.warning("Dosyada tablo bulunamadı.")
        else:
            for i, df in enumerate(tables):
                st.subheader(f"📋 Tablo {i+1}")
                st.dataframe(df, use_container_width=True)

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    f"📥 Tablo {i+1} indir (CSV)",
                    csv,
                    f"tablo_{i+1}.csv",
                    "text/csv",
                    key=f"download_{i}"
                )
                
            
      
            available_periods = []
            if len(tables) > 0:
                header_row = tables[0].columns.tolist()
                date_columns = [col for col in header_row if len(col.split('.')) == 3 and col.replace('.', '').isdigit()]
                available_periods = sorted(date_columns)  

            if available_periods:
                st.header("Bilanço Verileri için Dönem Seçimi")
                col_bs1, col_bs2 = st.columns(2)
                
                with col_bs1:
             
                    selected_period_end = st.selectbox(
                        "Bilanço Dönem Sonu Seçin",
                        available_periods,
                        index=len(available_periods)-1,
                        key="bs_end"
                    )
                
                with col_bs2:
              
                    bs_previous_periods = [p for p in available_periods if p < selected_period_end]
                    selected_period_start = st.selectbox(
                        "Bilanço Dönem Başı Seçin",
                        bs_previous_periods,
                        index=len(bs_previous_periods)-1 if bs_previous_periods else 0,
                        key="bs_start"
                    )
            else:
                st.warning("Bilanço tablolarında dönem bilgisi bulunamadı.")

 
            available_periods_other = []
            if len(tables) > 2:
                income_table = tables[2]
                header_row = income_table.columns.tolist()
                
                date_columns = [col for col in header_row 
                       if any(month in col for month in ["January", "February", "March", "April", 
                                                       "May", "June", "July", "August",
                                                       "September", "October", "November", "December"])
                       and any(year in col for year in ["2023", "2024", "2025"])]
                available_periods_other = sorted(date_columns)

            if available_periods_other:
                st.header("Gelir Tablosu için Dönem Seçimi")
                col_pl1, col_pl2 = st.columns(2)
                
                with col_pl1:
                    
                    selected_period_2_end = st.selectbox(
                        "Gelir Tablosu Dönem Sonu Seçin",
                        available_periods_other,
                        index=len(available_periods_other)-1,
                        key="pl_end"
                    )
                
                with col_pl2:
                 
                    pl_previous_periods = [p for p in available_periods_other if p < selected_period_2_end]
                    selected_period_2_start = st.selectbox(
                        "Gelir Tablosu Dönem Başı Seçin",
                        pl_previous_periods,
                        index=len(pl_previous_periods)-1 if pl_previous_periods else 0,
                        key="pl_start"
                    )
            else:
                st.warning("Gelir tablosunda dönem bilgisi bulunamadı.")

            try:
                if len(tables) > 1:
                    df2 = tables[1]
                    try:
                        kisaVadeli = clean_numeric(df2.loc[df2.iloc[:, 0] == "Short term borrowings", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Short term borrowings bulunamadı")
                    try:
                        kisaVadeliYukumlulukler = clean_numeric(df2.loc[df2.iloc[:, 0] == "TOTAL CURRENT LIABILITIES", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("TOTAL CURRENT LIABILITIES bulunamadı")
                    try:
                        uzunVadeliYukumlulukler = clean_numeric(df2.loc[df2.iloc[:, 0] == "TOTAL NON CURRENT LIABILITIES", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("TOTAL NON CURRENT LIABILITIES bulunamadı")
                    try:
                        calisanlaraIliskinYukumlulukler = clean_numeric(df2.loc[df2.iloc[:, 0] == "Liabilities for employee benefits", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Liabilities for employee benefits bulunamadı")
                    try:
                        kiralama_borclarinin_kisa_vadeli_kismi = clean_numeric(df2.loc[df2.iloc[:, 0] == "Lease liabilities", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Lease liabilities bulunamadı")
                    try:
                        uzun_vadeli_kiralama_borclari = clean_numeric(df2.loc[df2.iloc[:, 0] == "Long term lease liabilities", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Long term lease liabilities bulunamadı")
                    try:
                        uzun_vadeli_borclanma_kisa_vadeli = clean_numeric(df2.loc[df2.iloc[:, 0] == "Short term portion of long term borrowings", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Short term portion of long term borrowings bulunamadı")
                    try:
                        uzunVadeliBorc = clean_numeric(df2.loc[df2.iloc[:, 0] == "Long term borrowings", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Long term borrowings bulunamadı")
                    try:
                        ticariBorclar = clean_numeric(df2.loc[df2.iloc[:, 0] == "Trade payables", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Trade payables bulunamadı")    
                    try:
                        digerBorclar = clean_numeric(df2.loc[df2.iloc[:, 0] == "Other payables", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Other payables bulunamadı")   
                    try:
                        ertelenmisGelirler = clean_numeric(df2.loc[df2.iloc[:, 0] == "Deferred income to third parties", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Deferred income to third parties bulunamadı")   
                    try:
                        kisaVadeliKarsiliklar = clean_numeric(df2.loc[df2.iloc[:, 0] == "Short term provisions", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Short term provisions bulunamadı")                  
                    try:
                        ozKaynak = clean_numeric(df2.loc[df2.iloc[:, 0] == "TOTAL EQUITY", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("TOTAL EQUITY bulunamadı")
                
                if len(tables) > 0:
                    df1 = tables[0]
                    try:
                        nakitVb = clean_numeric(df1.loc[df1.iloc[:, 0] == "Cash and cash equivalents", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Cash and cash equivalents bulunamadı")
                    try:
                        ticariAlacaklar_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Trade receivables", selected_period_end].values[0])
                        ticariAlacaklar_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Trade receivables", selected_period_start].values[0])
                    except (IndexError, KeyError):
                        st.warning("Trade receivables bulunamadı")
                    try:
                        pesinOdenmisGiderler = clean_numeric(df1.loc[df1.iloc[:, 0] == "Prepaid expenses", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Prepaid expenses bulunamadı")
                    try:
                        stoklar_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Inventories", selected_period_end].values[0])
                        stoklar_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Inventories", selected_period_start].values[0])
                    except (IndexError, KeyError):
                        st.warning("Inventories bulunamadı")  
                    try:
                        digerDonenVarliklar = clean_numeric(df1.loc[df1.iloc[:, 0] == "Other current assests", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Other current assests bulunamadı") 
                    try:
                        donenVarliklar = clean_numeric(df1.loc[df1.iloc[:, 0] == "TOTAL CURRENT ASSETS", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("TOTAL CURRENT ASSETS bulunamadı")    
                    try:
                        duranVarliklar = clean_numeric(df1.loc[df1.iloc[:, 0] == "TOTAL NON CURRENT ASSETS", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("TOTAL NON CURRENT ASSETS bulunamadı")
                    try:
                        toplamVarliklar = clean_numeric(df1.loc[df1.iloc[:, 0] == "TOTAL ASSETS", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("TOTAL ASSETS bulunamadı")                           
                    try:
                        finansalYatirimlar = clean_numeric(df1.loc[df1.iloc[:, 0] == "Financial investments", selected_period_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Financial investments bulunamadı")

                if len(tables) > 2:
                    df3 = tables[2]
                    try:
                        netKar = clean_numeric(df3.loc[df3.iloc[:, 0] == "Profit / (loss) for the period", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Profit / (loss) for the period bulunamadı")
                    try:
                        vergiOncesiFaaliyetKariZarari = clean_numeric(df3.loc[df3.iloc[:, 0] == "Profit / (loss) before tax", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Profit / (loss) before tax bulunamadı")
                    try:
                        donemOncesiVergiGelirGideri = clean_numeric(df3.loc[df3.iloc[:, 0] == "Current tax expense for the year", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Current tax expense for the year bulunamadı")
                    try:
                        hasilat = clean_numeric(df3.loc[df3.iloc[:, 0] == "Revenue", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Revenue bulunamadı")
                    try:
                        finansmanGiderleri = clean_numeric(df3.loc[df3.iloc[:, 0] == "Financial expense (-)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Financial expense (-) bulunamadı")
                    try:
                        finansmanGelirleri = clean_numeric(df3.loc[df3.iloc[:, 0] == "Financial income", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Financial income bulunamadı")
                    try:
                        satilanMalinMaliyeti = clean_numeric(df3.loc[df3.iloc[:, 0] == "Cost of sales (-)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Cost of sales (-) bulunamadı")
                    try:
                        brutKar = clean_numeric(df3.loc[df3.iloc[:, 0] == "Gross profit / (loss)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Gross profit / (loss) bulunamadı")
                    try:
                        genelYonetimGiderleri = clean_numeric(df3.loc[df3.iloc[:, 0] == "General and administrative expenses (-)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("General and administrative expenses (-) bulunamadı")
                    try:
                        pazarlamaGiderleri = clean_numeric(df3.loc[df3.iloc[:, 0] == "Selling, marketing and distribution expenses (-)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Selling, marketing and distribution expenses (-) bulunamadı")
                    try:
                        argeGiderleri = clean_numeric(df3.loc[df3.iloc[:, 0] == "Research and development expenses (-)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Research and development expenses (-) bulunamadı")
                    try:
                        amortismanVeItfaPaylari = clean_numeric(df3.loc[df3.iloc[:, 0] == "Operating profit / (loss)", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Operating profit / (loss) bulunamadı")
                    try:
                        hisseBasiKar = clean_numeric(df3.loc[df3.iloc[:, 0] == "Earnings per share from continuing operations", selected_period_2_end].values[0])
                    except (IndexError, KeyError):
                        st.warning("Earnings per share from continuing operations bulunamadı")
                        
            except Exception as e:
                st.error(f"Tablo verileri işlenirken hata: {str(e)}")

    except Exception as e:
        st.error(f"Dosya işlenirken hata: {str(e)}")


selected_module = st.selectbox(
    "Modül Seçimi:",
    ("Çarpan Hesaplama Modülü", "DCF / İNA Hesaplama", "Finansal Rasyolar ve Analiz", "Grafik ve Raporlama Modülü"),
    key="module_select"
) 


if selected_module != "Lütfen bir modül seçiniz":
    if st.button("Getir", key="getir_button"):
        st.session_state['selected_module'] = selected_module
        st.session_state['show_module'] = True


if st.session_state.get('show_module', False) and uploaded_file:
    if st.session_state['selected_module'] == "Çarpan Hesaplama Modülü":
        st.title("📊 Çarpan Hesaplama Modülü")
        
  
        piyasa_fiyati = st.number_input("Piyasa Fiyatı (USD)", value=10.0, min_value=0.0, key="piyasa_fiyati")
        pay_lot, ek_pay_lot = get_hisse_lotlari()

        if st.button("Hesapla", key="hesapla_button"):
            st.title("Şirketin ve Rakip Şirketlerin Oranları")
            try:
                toplam_hisse = pay_lot + ek_pay_lot
                
                hisseBasiKar = hisseBasiKar/10
                fk = fk_orani(piyasa_fiyati, hisseBasiKar)
                fd_favok = fddividefavok(  
                    kisaVadeli, 
                    uzun_vadeli_borclanma_kisa_vadeli, 
                    kiralama_borclarinin_kisa_vadeli_kismi,
                    uzunVadeliBorc, 
                    uzun_vadeli_kiralama_borclari,
                    netKar, 
                    finansmanGiderleri, 
                    amortismanVeItfaPaylari,
                    donemOncesiVergiGelirGideri, 
                    piyasa_fiyati,  
                    toplam_hisse, 
                    nakitVb, 
                    finansalYatirimlar
                )           
                pd_dd = pd_divided_dd(pay_lot, ek_pay_lot, piyasa_fiyati, ozKaynak)
                favok = netKar + donemOncesiVergiGelirGideri + finansmanGiderleri + amortismanVeItfaPaylari

             
                col1, col2, col3 = st.columns(3)

                symbol = "5263.TWO"
                ticker = yf.Ticker(symbol)
                info = ticker.info

                symbol2 = "IMMR"
                ticker2 = yf.Ticker(symbol2)
                info2 = ticker2.info

                symbol3 = "DBO.TO"
                ticker3 = yf.Ticker(symbol3)
                info3 = ticker3.info

                with col1:
                    st.metric("📈 Şirketin F/K Oranı", 
                            f"{fk:.2f}x" if fk is not None else "Hesaplanamadı",
                            help="Piyasa Fiyatı / Hisse Başı Kar")
                    st.metric(f"📈 {symbol} F/K Oranı", 
                            f"{info.get("trailingPE"):.2f}x" if info.get("trailingPE") is not None else "Hesaplanamadı",
                            help="Piyasa Fiyatı / Hisse Başı Kar")
                    st.metric(f"📈 {symbol2} F/K Oranı", 
                            f"{info2.get("trailingPE"):.2f}x" if info2.get("trailingPE") is not None else "Hesaplanamadı",
                            help="Piyasa Fiyatı / Hisse Başı Kar")
                    st.metric(f"📈 {symbol3} F/K Oranı", 
                            f"{info3.get("trailingPE"):.2f}x" if info3.get("trailingPE") is not None else "Hesaplanamadı",
                            help="Piyasa Fiyatı / Hisse Başı Kar")
                    
                    valid_values = [pe for pe in [info.get("trailingPE"), info2.get("trailingPE"), info3.get("trailingPE")] if pe is not None]
                    # Medyanı hesapla
                    if valid_values:
                        median_pe = np.median(valid_values)
                        st.metric("📊 Medyan F/K Oranı", f"{median_pe:.2f}x", help="Üç hissenin F/K oranlarının ortanca değeri")
                    else:
                        st.warning("Hiçbir geçerli F/K oranı bulunamadı.")

                enterprise_value = info.get("enterpriseValue")
                ebitda = info.get("ebitda")
                ev_ebitda = enterprise_value / ebitda

                enterprise_value2 = info2.get("enterpriseValue")
                ebitda2 = info2.get("ebitda")
                ev_ebitda2 = enterprise_value2 / ebitda2

                enterprise_value3 = info3.get("enterpriseValue")
                ebitda3 = info3.get("ebitda")
                ev_ebitda3 = enterprise_value3 / ebitda3

                with col2:
                    st.metric("📊 Şirketin FD/FAVOK", 
                            f"{fd_favok:.2f}x" if fd_favok is not None else "Hesaplanamadı",
                            help="Firma Değeri / FAVOK")
                    st.metric(f"📈 {symbol} FD/FAVOK", 
                            f"{ev_ebitda:.2f}x" if ev_ebitda is not None else "Hesaplanamadı",
                            help="Firma Değeri / FAVOK")
                    st.metric(f"📈 {symbol2} FD/FAVOK", 
                            f"{ev_ebitda2:.2f}x" if ev_ebitda2 is not None else "Hesaplanamadı",
                            help="Firma Değeri / FAVOK")
                    st.metric(f"📈 {symbol3} FD/FAVOK", 
                            f"{ev_ebitda3:.2f}x" if ev_ebitda3 is not None else "Hesaplanamadı",
                            help="Firma Değeri / FAVOK")
                    valid_values2 = [pe for pe in [ev_ebitda, ev_ebitda2, ev_ebitda3] if pe is not None]
                    # Medyanı hesapla
                    if valid_values2:
                        median_pe2 = np.median(valid_values2)
                        st.metric("📊 Medyan FD/FAVOK", f"{median_pe2:.2f}x", help="Üç hissenin FD/FAVOK oranlarının ortanca değeri")
                    else:
                        st.warning("Hiçbir geçerli FD/FAVOK oranı bulunamadı.")

                    
                
                with col3:
                    st.metric("📉 Şirketin PD/DD", 
                            f"{pd_dd:.2f}x" if pd_dd is not None else "Hesaplanamadı",
                            help="Piyasa Değeri / Defter Değeri")
                    st.metric(f"📈 {symbol} PD/DD", 
                            f"{info.get("priceToBook"):.2f}x" if info.get("priceToBook") is not None else "Hesaplanamadı",
                            help="Piyasa Değeri / Defter Değeri")
                    st.metric(f"📈 {symbol2} PD/DD", 
                            f"{info2.get("priceToBook"):.2f}x" if info2.get("priceToBook") is not None else "Hesaplanamadı",
                            help="Piyasa Değeri / Defter Değeri")
                    st.metric(f"📈 {symbol3} PD/DD", 
                            f"{info3.get("priceToBook"):.2f}x" if info3.get("priceToBook") is not None else "Hesaplanamadı",
                            help="Piyasa Değeri / Defter Değeri")
                    valid_values3 = [pe for pe in [info.get("priceToBook"), info2.get("priceToBook"), info3.get("priceToBook")] if pe is not None]
                    # Medyanı hesapla
                    if valid_values3:
                        median_pe3 = np.median(valid_values3)
                        st.metric("📊 Medyan PD/DD", f"{median_pe3:.2f}x", help="Üç hissenin PD/DD oranlarının ortanca değeri")
                    else:
                        st.warning("Hiçbir geçerli PD/DD oranı bulunamadı.")

               
                st.session_state.update({
                    'fk': fk,
                    'fd_divide_favok': fd_favok,
                    'pd_divide_dd': pd_dd
                })

            except Exception as e:
                st.error(f"Hesaplama hatası: {str(e)}")
                
    elif st.session_state['selected_module'] == "DCF / İNA Hesaplama":
        st.title("📊 DCF / İNA Hesaplama")
    
    
        available_periods = []
        if len(tables) > 0:
       
            header_row = tables[0].columns.tolist()
        
            date_columns = [col for col in header_row if re.match(r'^\d{2}\.\d{2}\.\d{4}$', col)]
            available_periods = sorted(date_columns, reverse=True)  
    
    
        col1, col2 = st.columns(2)
    
        with col1:
        
            period_end = st.selectbox(
            "Dönem Sonu Tarihini Seçin",
                available_periods,
                index=0,
                key="dcf_period_end"
            )
            stoklar_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Inventories", period_end].values[0])

            ticariAlacaklar_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Trade receivables", period_end].values[0])

            pesinOdenmisGiderler_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Prepaid expenses", period_end].values[0])

            ticariBorclar_son = clean_numeric(df2.loc[df2.iloc[:, 0] == "Trade payables", period_end].values[0])

            pesinOdenmisGiderler_son = clean_numeric(df2.loc[df2.iloc[:, 0] == "Trade payables", period_end].values[0])

            ertelenmisGelirler_son = clean_numeric(df2.loc[df2.iloc[:, 0] == "Deferred income to third parties", period_end].values[0])
  
            digerDonenVarliklar_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Other current assests", period_end].values[0])
  
            maddiDuranVarlik_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Property, plant and equipment", period_end].values[0])

            maddiOlmayanDuranVarlik_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "Intangible assets", period_end].values[0])

            donenVarliklar_son = clean_numeric(df1.loc[df1.iloc[:, 0] == "TOTAL CURRENT ASSETS", period_end].values[0])

            kisaVadeliYukumlulukler_son = clean_numeric(df2.loc[df2.iloc[:, 0] == "TOTAL CURRENT LIABILITIES", period_end].values[0])

            digerBorclar_son = clean_numeric(df2.loc[df2.iloc[:, 0] == "Other payables", period_end].values[0])


    
        with col2:
      
            filtered_periods = [d for d in available_periods if d < period_end]
        
            if not filtered_periods:
                st.warning("Dönem başı için uygun tarih bulunamadı")
                period_start = None
            else:
                period_start = st.selectbox(
                "Dönem Başı Tarihini Seçin",
                    filtered_periods,
                    index=0,
                    key="dcf_period_start"
                )
                stoklar_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Inventories", period_start].values[0])

                ticariAlacaklar_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Trade receivables", period_start].values[0])

                pesinOdenmisGiderler_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Prepaid expenses", period_start].values[0])

                ticariBorclar_bas = clean_numeric(df2.loc[df2.iloc[:, 0] == "Trade payables", period_start].values[0])

                ertelenmisGelirler_bas= clean_numeric(df2.loc[df2.iloc[:, 0] == "Deferred income to third parties", period_start].values[0])

                digerDonenVarliklar_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Other current assests", period_start].values[0])

                maddiDuranVarlik_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Property, plant and equipment", period_start].values[0])

                maddiOlmayanDuranVarlik_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "Intangible assets", period_start].values[0])

                donenVarliklar_bas = clean_numeric(df1.loc[df1.iloc[:, 0] == "TOTAL CURRENT ASSETS", period_start].values[0])

                kisaVadeliYukumlulukler_bas = clean_numeric(df2.loc[df2.iloc[:, 0] == "TOTAL CURRENT LIABILITIES", period_start].values[0])

                digerBorclar_bas = clean_numeric(df2.loc[df2.iloc[:, 0] == "Other payables", period_start].values[0])

        ebit = brutKar - ((genelYonetimGiderleri+ pazarlamaGiderleri + argeGiderleri)*-1)

        amortisman_raw = st.text_input(
            "Yıllık Amortisman Tutarı (₺)", 
            value="913.657",  
            key="amortisman_input"
        )
        cleaned_input = re.sub(r"[^\d]", "", amortisman_raw)  
        try:
            amortisman = int(cleaned_input)
        except ValueError:
            amortisman = 0
        amortisman_formatted = f"{amortisman:,}".replace(",", ".")
        st.write(f"📌 Girilen Amortisman Tutarı: {amortisman_formatted} ₺")

        nwcDegisim_bas = nwcdegisim(donenVarliklar_bas, kisaVadeliYukumlulukler_bas)
        nwcDegisim_son = nwcdegisim(donenVarliklar_son, kisaVadeliYukumlulukler_son)
        nwcDegisim = nwcDegisim_son - nwcDegisim_bas
        st.success(f"📊 ΔNWC: **{format_number(nwcDegisim, 2)}**")
        st.success(f"📊 EBIT: **{format_number(ebit, 2)}**")
        st.success(f"📊 Amortisman: **{format_number(amortisman, 2)}**")
        capexDegeri =  2846728
        st.success(f"📊 Capex: **{format_number(capexDegeri, 2)}**")
        vergiOrani = vergiorani(donemOncesiVergiGelirGideri, vergiOncesiFaaliyetKariZarari)  
        st.success(f"📊 Vergi Oranı: **{format_number(vergiOrani, 2)}**")
        fcfDegeri = fcf(nwcDegisim, capexDegeri, ebit, amortisman, donemOncesiVergiGelirGideri)
        st.success(f"📊 FCF: **{format_number(fcfDegeri, 2)}**")

        st.subheader("Yıllık Faaliyet Karı Tahminleri")
        faaliyet_kari = []
        for yil in range(1, 6):
            faaliyetKari_raw = st.text_input(
                f"{yil}. Yıl Faaliyet Karı Tahmini (USD)", 
                value=0,  
                key=f"faaliyetkari_{yil}"
            )
            try:
                faaliyetKari = int(faaliyetKari_raw.replace(".", "").replace(",", "")) 
            except ValueError:
                faaliyetKari = 0
            faaliyet_kari.append(faaliyetKari)


        st.subheader("Yıllık Amortisman Tahminleri")
        amortisman_degerleri = []
        for yil in range(1, 6):
            amortismanRaw = st.text_input(
                f"{yil}. Yıl Amortisman Tahmini (USD)", 
                value=0,  
                key=f"amortisman_{yil}"
            )
            try:
                amortisman = int(amortismanRaw.replace(".", "").replace(",", "")) 
            except ValueError:
                amortisman = 0
            amortisman_degerleri.append(amortisman)

        st.subheader("Yıllık Ödenen Vergi Tahminleri")
        odenen_vergi = []
        for yil in range(1, 6):
            odenenVergiRaw = st.text_input(
                f"{yil}. Yıl Ödenen Vergi Tahmini (USD)", 
                value=0,  
                key=f"odenenvergi_{yil}"
            )
            try:
                odenenVergi = int(odenenVergiRaw.replace(".", "").replace(",", "")) 
            except ValueError:
                odenenVergi = 0
            odenen_vergi.append(odenenVergi)

        st.subheader("Yıllık ΔNWC Tahminleri")
        delta_NWC = []
        for yil in range(1, 6):
            deltaNWCRaw = st.text_input(
                f"{yil}. Yıl ΔNWC Tahmini (USD)", 
                value=0,  
                key=f"deltanwc_{yil}"
            )
            try:
                deltaNWC = int(deltaNWCRaw.replace(".", "").replace(",", ""))
            except ValueError:
                deltaNWC = 0
            delta_NWC.append(deltaNWC)

        st.subheader("Yıllık Capex Tahminleri")
        capex_degerleri = []
        for yil in range(1, 6):
            capexRaw_= st.text_input(
                f"{yil}. Yıl Capex Tahmini (USD)", 
                value=0,  
                key=f"capex_{yil}"
            )
            try:
                capex_ = int(capexRaw_.replace(".", "").replace(",", ""))
            except ValueError:
                capex_ = 0
            capex_degerleri.append(capex_)


        terminal_buyume = st.session_state.get('terminal_buyume')
        terminal_buyume = st.number_input(  
        "Terminal Büyüme Oranı (%) (10. yıldan sonra)", 
            min_value=0.0, 
            max_value=100.0, 
            step=0.1, 
            value=2.5
        ) / 100


        besYillikfcf = bes_yillik_fcf(faaliyet_kari, amortisman_degerleri, odenen_vergi, delta_NWC, capex_degerleri)

        terminal_fcf = besYillikfcf[-1] * (1 + terminal_buyume)


        st.success("📊 5 Yıllık FCF Tahminleri:")
        for yil, fcf in enumerate(besYillikfcf, 1):
            st.success(f"{yil}. Yıl FCF: {format_number(fcf, 2)}")

        st.success(f"Terminal FCF (5. Yıl Sonrası): {terminal_fcf:.2f}")
      
        st.session_state['besYillikfcf'] = besYillikfcf
        st.session_state['terminal_fcf'] = terminal_fcf 
        st.subheader("Yıllık İndirgeme Oranı")
        indirgeme_degerleri = []
        for yil in range(1, 6):
            indirgeme_orani = st.number_input(
                f"{yil}. Yıl İndirgeme Oranı (%)", 
                value=50.0,  
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                key=f"indirgemeorani_{yil}"
            )
            indirgeme_degerleri.append(indirgeme_orani / 100)  

        besYillikIndirgemeliDegerler = bes_yillik_indirgeme(besYillikfcf, indirgeme_degerleri)
        st.session_state['besYillikIndirgemeliDegerler'] = besYillikIndirgemeliDegerler
        def format_number(sayi, ondalik=2):
            try:
                return f"{sayi:,.{ondalik}f}"
            except (TypeError, ValueError):
                return "Invalid"

        formatted_values = [format_number(x, 2) for x in besYillikIndirgemeliDegerler]

        st.success(f"📊 Bugünkü Değerler (NPV): {', '.join(formatted_values)}")

        npvToplam = 0
        for i in range(5):
            npvToplam += besYillikIndirgemeliDegerler[i]
        st.success(f"📊 Bugunkü Değerler (NPV) Toplamı: {format_number(npvToplam, 2)}")
        netBorc = (kisaVadeli + uzun_vadeli_borclanma_kisa_vadeli + kiralama_borclarinin_kisa_vadeli_kismi + uzunVadeliBorc + uzun_vadeli_kiralama_borclari) - nakitVb - finansalYatirimlar
        st.session_state['netBorc'] = netBorc
        st.success(f"📊 Net Borç : **{format_number(netBorc, 2)}**")
        wacc = 0.1318  # Varsayılan WACC değeri
        terminalDegeri = terminal_degeri(besYillikfcf, terminal_buyume, wacc)
        st.session_state['terminalDegeri'] = terminalDegeri
        st.success(f"📊 Terminal Değeri: **{format_number(terminalDegeri, 2)}**")


        toplamSirketDegeri = sum(besYillikIndirgemeliDegerler) + terminalDegeri
        st.success(f"📊 Şirket Değeri : **{format_number(toplamSirketDegeri, 2)}**")
        st.session_state['toplamSirketDegeri'] = toplamSirketDegeri
        toplamFirmaDegeri = sum(besYillikIndirgemeliDegerler) + terminalDegeri - netBorc
        st.session_state['toplamFirmaDegeri'] = toplamFirmaDegeri
        st.success(f"📊 Firma Değeri : **{format_number(toplamFirmaDegeri, 2)}**")


    elif st.session_state['selected_module'] == "Finansal Rasyolar ve Analiz":
        st.title("📈 Finansal Rasyolar ve Analiz Modülü")
        st.title("📈 Likidite Oranları")
        cariOran = carioran(donenVarliklar, kisaVadeliYukumlulukler)
        st.session_state['cariOran'] = cariOran
        st.success(f"📊 Cari Oran: **{cariOran:.2f}**")
        asitTestOrani = asittestorani(donenVarliklar, stoklar_son, kisaVadeli, uzun_vadeli_borclanma_kisa_vadeli, ticariBorclar, calisanlaraIliskinYukumlulukler, digerBorclar, ertelenmisGelirler, kisaVadeliKarsiliklar)
        st.session_state['asitTestOrani'] = asitTestOrani
        st.success(f"📊 Asit - Test Oranı: **{asitTestOrani:.2f}**")

        st.title("📈 Borçluluk Oranı")
        borcToplamVarlik = borctoplamvarlik(donenVarliklar, duranVarliklar, kisaVadeliYukumlulukler, uzunVadeliYukumlulukler)
        st.session_state['borcToplamVarlik'] = borcToplamVarlik
        st.success(f"📊 Borç / Toplam Varlık: %**{borcToplamVarlik:.2f}**")

        st.title("📈 Karlılık Değerleri")
        netKarMarji = netkarmarji(netKar, hasilat)
        st.session_state['netKarMarji'] = netKarMarji
        st.success(f"📊 Net Kar Marjı: %**{netKarMarji:.2f}**")
        aktifKarlilikOrani = aktifkarlilik(netKar, donenVarliklar, duranVarliklar)
        st.session_state['aktifKarlilikOrani'] = aktifKarlilikOrani
        st.success(f"📊 Aktif Karlılık Oranı: %**{aktifKarlilikOrani:.2f}**")
        ozSermayeKarliligi = ozsermayekarliligi(netKar, ozKaynak)
        st.session_state['ozSermayeKarliligi'] = ozSermayeKarliligi
        st.success(f"📊 Öz Sermaye Karlılığı: %**{ozSermayeKarliligi:.2f}**")

        st.title("📈 Faaliyet Değerleri")
        alacakDevirHizi = alacakdevirhizi(hasilat, ticariAlacaklar_son)
        st.session_state['alacakDevirHizi'] = alacakDevirHizi
        st.success(f"📊 Alacak Devir Hızı: **{alacakDevirHizi:.2f}**")
        stokDevirHizi = stokdevirhizi(satilanMalinMaliyeti, stoklar_son)
        stokDevirHizi*=-1
        st.session_state['stokDevirHizi'] = stokDevirHizi
        st.success(f"📊 Stok Devir Hızı: **{stokDevirHizi:.2f}**")   

    elif st.session_state['selected_module'] == "Grafik ve Raporlama Modülü":
        st.title("📊 Grafik ve Raporlama Modülü")
        st.info("Finansal Analiz Grafikleri ve Raporları")

        report_figs = []

        st.subheader("📈 Finansal Grafikler")


        with st.expander("Değerleme Çarpanları"):
            fig = draw_valuation_multiples_chart()
            if fig:
                st.pyplot(fig)
                report_figs.append(("Değerleme Çarpanları", fig))

        with st.expander("Nakit Akımı Analizi"):
            col1, col2 = st.columns(2)
            with col1:
                fig = draw_fcf_chart()
                if fig:
                    st.pyplot(fig)
                    report_figs.append(("5 Yıllık FCF Tahminleri", fig))
        
            with col2:
                fig = draw_dcf_chart()
                if fig:
                    st.pyplot(fig)
                    report_figs.append(("İndirgemeli Nakit Akımları", fig))
        
            fig = draw_terminal_value_chart()
            if fig:
                st.pyplot(fig)
                report_figs.append(("Terminal Değer Dağılımı", fig))

     
        with st.expander("Finansal Oranlar"):
            col1, col2 = st.columns(2)
            with col1:
                fig = draw_liquidity_chart()
                if fig:
                    st.pyplot(fig)
                    report_figs.append(("Likidite Oranları", fig))
            
                fig = draw_debt_chart()
                if fig:
                    st.pyplot(fig)
                    report_figs.append(("Borçluluk Oranı", fig))
        
            with col2:
                fig = draw_profitability_chart()
                if fig:
                    st.pyplot(fig)
                    report_figs.append(("Karlılık Oranları", fig))
            
                fig = draw_activity_chart()
                if fig:
                    st.pyplot(fig)
                    report_figs.append(("Faaliyet Oranları", fig))

        
        with st.expander("Finansal Metrikler"):
            fig = draw_financial_metrics_chart()
            if fig:
                st.pyplot(fig)
                report_figs.append(("Finansal Metrikler", fig))

        st.divider()
        st.subheader("📑 Rapor Oluşturma")

        if st.button("📊 PDF Raporu Oluştur"):
            with st.spinner("Rapor oluşturuluyor..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    if create_pdf_report(tmp_pdf.name, report_figs):
                        with open(tmp_pdf.name, "rb") as f:
                            st.download_button(
                                label="📥 PDF Raporunu İndir",
                                data=f,
                                file_name="finansal_analiz_raporu.pdf",
                                mime="application/pdf"
                            )
                        st.success("Rapor başarıyla oluşturuldu!")
                    else:
                        st.error("PDF oluşturulamadı! Lütfen verileri kontrol edin.")