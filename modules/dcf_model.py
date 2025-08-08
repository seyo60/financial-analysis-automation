import streamlit as st
def nwcdegisim(donenVarliklar, kisaVadeliYukumlulukler):
    try:
        return donenVarliklar - kisaVadeliYukumlulukler
    except Exception as e:
        raise ValueError(f"NWC değişim hesaplanırken hata: {str(e)}")


def capex(maddiDuranVarlik_son, maddiDuranVarlik_bas, maddiOlmayanDuranVarlik_son, maddiOlmayanDuranVarlik_bas, amortisman):
    try:
        return (maddiDuranVarlik_son - maddiDuranVarlik_bas) + (maddiOlmayanDuranVarlik_son - maddiOlmayanDuranVarlik_bas) + amortisman
    except Exception as e:
        raise ValueError(f"Capex hesaplanırken hata: {str(e)}")

def vergiorani(donemOncesiVergiGelirGideri, vergiOncesiFaaliyetKariZarari): 
    try:
        return (donemOncesiVergiGelirGideri / vergiOncesiFaaliyetKariZarari) 
    except Exception as e:
        raise ValueError(f"Vergi oranı hesaplanırken hata: {str(e)}")

def fcf(nwc_degisim, capex, ebit, amortisman, donemOncesiVergiGelirGideri):
    try:
        return ebit - donemOncesiVergiGelirGideri + amortisman - nwc_degisim - capex
    except Exception as e:
        raise ValueError(f"FCF hesaplanırken hata: {str(e)}")

def bes_yillik_fcf(faaliyet_kari, amortisman_degerleri, odenen_vergi, delta_NWC, capex_degerleri):
    fcf_listesi = []

    try:
        for i in range(5):
            fcf = (faaliyet_kari[i]
                   + amortisman_degerleri[i]
                   - odenen_vergi[i]
                   - delta_NWC[i]
                   - capex_degerleri[i])
            fcf_listesi.append(fcf)
    except IndexError as e:
        print(f"İndeks hatası: Listenin boyutları 5 yıl için yeterli olmayabilir. Hata: {e}")
    except TypeError as e:
        print(f"Tip hatası: Girdi türleri uygun değil. Hata: {e}")
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")

    return fcf_listesi


def bes_yillik_indirgeme(fcf_listesi, indirgeme_degerleri):
    indirgeme_deger_listesi = []
    for i in range(min(len(fcf_listesi), len(indirgeme_degerleri))):
        try:
            oran = indirgeme_degerleri[i]
            if oran > 1:  # % olarak girildiyse düzelt (örneğin 89.93 → 0.8993)
                oran = oran / 100

            # DCF formülü yerine doğrudan çarpım:
            indirgemeli_deger =  (fcf_listesi[i] * oran)
            indirgeme_deger_listesi.append(round(indirgemeli_deger, 2))
        except (TypeError, IndexError, ZeroDivisionError):
            indirgeme_deger_listesi.append(0)
    return indirgeme_deger_listesi


def terminal_degeri(fcf_listesi, buyume_orani, wacc):
    try:
        # Son FCF değerini al
        son_fcf = float(fcf_listesi[-1])
        
        # Büyüme oranını işle (liste veya tek değer)
        terminal_buyume = buyume_orani[-1] if isinstance(buyume_orani, list) else float(buyume_orani)
        
        # WACC ve büyüme oranını kontrol et
        if wacc <= terminal_buyume:
            raise ValueError("WACC, terminal büyüme oranından büyük olmalıdır")
        
        # Terminal değer = [FCF * (1+g)] / (WACC - g)
        terminal_deger = (son_fcf * (1 + terminal_buyume)) / (wacc - terminal_buyume)
        
        # Terminal değeri bugüne indirgeme: / (1+WACC)^n
        n = len(fcf_listesi)  # Projeksiyon yılı (genelde 5)
        terminal_deger_indirgenmis = terminal_deger / ((1 + wacc) ** n)
        
        return terminal_deger_indirgenmis
        
    except (IndexError, ValueError, TypeError) as e:
        raise ValueError(f"Terminal değer hesaplanamadı: {str(e)}")
    
    except IndexError:
        raise ValueError("FCF listesi boş olamaz")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Geçersiz giriş değeri: {str(e)}")
