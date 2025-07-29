def toplam_hisse(pay_lot, ek_pay_lot):
    try:
        return (pay_lot if pay_lot is not None else 0) + (ek_pay_lot if ek_pay_lot is not None else 0)
    except Exception as e:
        raise ValueError(f"Toplam hisse hesaplanırken hata: {str(e)}")
    
def fk_orani(piyasa_fiyati: float, hisseBasiKar: float) -> float:
    try:
        return piyasa_fiyati / hisseBasiKar
    except Exception as e:
        raise ValueError(f"F/K hesaplanırken hata: {str(e)}")


def fd_divide_favok(
    kisaVadeli: float,
    uzun_vadeli_borclanma_kisa_vadeli: float,
    kiralama_borclarinin_kisa_vadeli_kismi: float,
    uzunVadeliBorc: float,
    uzun_vadeli_kiralama_borclari: float,
    net_kar: float,
    finansman_giderleri: float,
    amortismanVeItfaPaylari: float,
    donemOncesiVergiGelirGideri: float,
    piyasa_fiyati: float,
    toplam_hisse: int,
    nakit: float,
    finansal_yatirimlar: float
) -> float:
    try:
        # Temel kontroller
        if toplam_hisse <= 0 or piyasa_fiyati <= 0:
            return None

        # Piyasa değeri hesaplama
        piyasa_degeri = piyasa_fiyati * toplam_hisse
        
        # Net borç hesaplama
        toplam_borc = (kisaVadeli + uzun_vadeli_borclanma_kisa_vadeli + 
                       kiralama_borclarinin_kisa_vadeli_kismi + uzunVadeliBorc + uzun_vadeli_kiralama_borclari)
        net_borc = toplam_borc - (nakit + finansal_yatirimlar)

        

        fd = piyasa_degeri + net_borc
        
        # Firma değeri
        firma_degeri = piyasa_degeri + net_borc
        
        # FAVOK hesaplama
        favok = net_kar + donemOncesiVergiGelirGideri + finansman_giderleri + amortismanVeItfaPaylari

        
        # Oranın anlamlı olması için kontrol
        if favok <= 0 or firma_degeri <= 0:
            return None
            
        return fd / favok
        
    except Exception as e:
        raise ValueError(f"FD/FAVOK hesaplanırken hata: {str(e)}")


def pd_divide_dd(
    pay_lot: int, 
    ek_pay_lot: int, 
    piyasa_fiyati: float, 
    oz_kaynak: float
) -> float:
    try:
        # Toplam hisse ve değer kontrolleri
        toplam_hisse = pay_lot + ek_pay_lot
        if toplam_hisse <= 0 or oz_kaynak <= 0 or piyasa_fiyati <= 0:
            return None
            
        piyasa_degeri = piyasa_fiyati * toplam_hisse
        return piyasa_degeri / oz_kaynak
        
    except Exception as e:
        raise ValueError(f"PD/DD hesaplanırken hata: {str(e)}")
    
def carioran(donenVarliklar, kisaVadeliYukumlulukler):
    try:
        return (donenVarliklar)/(kisaVadeliYukumlulukler)
    except Exception as e:
        raise ValueError(f"Cari oran hesaplanırken hata: {str(e)}")


def asittestorani(donenVarliklar, stoklar, kisaVadeli, uzun_vadeli_borclanma_kisa_vadeli, ticariBorclar, calisanlaraIliskinYukumlulukler, digerBorclar, ertelenmisGelirler, kisaVadeliKarsiliklar):
    try:
        return (donenVarliklar-stoklar)/(kisaVadeli + uzun_vadeli_borclanma_kisa_vadeli + ticariBorclar + calisanlaraIliskinYukumlulukler + digerBorclar + ertelenmisGelirler + kisaVadeliKarsiliklar)
    except Exception as e:
        raise ValueError(f"Asit - Test oranı hesaplanırken hata: {str(e)}")
def borctoplamvarlik(donenVarliklar, duranVarliklar, kisaVadeliYukumlulukler, uzunVadeliYukumlulukler):
    try:
        return ((kisaVadeliYukumlulukler + uzunVadeliYukumlulukler)/(donenVarliklar + duranVarliklar))*100
    except Exception as e:
        raise ValueError(f"Borç / Toplam varlık hesaplanırken hata: {str(e)}")

def finansalkaldiracorani(kisaVadeliYukumlulukler, uzunVadeliYukumlulukler, toplamVarliklar):
    try:
        return (kisaVadeliYukumlulukler + uzunVadeliYukumlulukler)/(toplamVarliklar)
    except Exception as e:
        raise ValueError(f"Finansal kaldıraç hesaplanırken hata: {str(e)}")

def netkarmarji(netKar, hasilat):
    try:
        return (netKar/hasilat)
    except Exception as e:
        raise ValueError(f"Net kar marjı hesaplanırken hata: {str(e)}")

def aktifkarlilik(netKar, donenVarlik, duranVarlik):
    try:
        return (netKar/(donenVarlik + duranVarlik))
    except Exception as e:
        raise ValueError(f"Aktif karlılık hesaplanırken hata: {str(e)}")

def ozsermayekarliligi(netKar, ozKaynak):
    try:
        return (netKar / ozKaynak)
    except Exception as e:
        raise ValueError(f"Öz sermaye karlılığı hesaplanırken hata: {str(e)}")
    
def alacakdevirhizi(hasilat, ticariAlacaklar_son):
    try:
        return 365/(ticariAlacaklar_son/hasilat*365)
    except Exception as e:
        raise ValueError(f"Alacak devir hızı hesaplanırken hata: {str(e)}")
    
def stokdevirhizi(satilanMalinMaliyeti, stoklar_son):
    try:
        return 365/(stoklar_son/satilanMalinMaliyeti*365)
    except Exception as e:
        raise ValueError(f"Stok devir hızı hesaplanırken hata: {str(e)}")