from fpdf import FPDF
import matplotlib.pyplot as plt
import tempfile
import streamlit as st
import os
import gc

class SimpleFPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Font dosyaları için göreceli yol (modules/fonts altında)
            font_dir = os.path.join(os.path.dirname(__file__), "..", "modules", "fonts")
            
            # Font dosya yolları
            font_path_regular = os.path.join(font_dir, "DejaVuSans.ttf")
            font_path_bold = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
            
            # Fontların var olup olmadığını kontrol et
            if not os.path.exists(font_path_regular):
                raise FileNotFoundError(f"DejaVuSans.ttf bulunamadı: {font_path_regular}")
            if not os.path.exists(font_path_bold):
                raise FileNotFoundError(f"DejaVuSans-Bold.ttf bulunamadı: {font_path_bold}")
            
            # Fontları PDF'e ekle (Türkçe karakter desteği için uni=True)
            self.add_font('DejaVu', '', font_path_regular, uni=True)
            self.add_font('DejaVu', 'B', font_path_bold, uni=True)
            self.set_font('DejaVu', '', 12)
            
        except Exception as e:
            st.error(f"Font yükleme hatası: {str(e)}")
            # Yedek font ayarı
            try:
                # Arial Unicode MS varsa onu dene
                arial_path = os.path.join(font_dir, "arial-unicode-ms.ttf")
                if os.path.exists(arial_path):
                    self.add_font('ArialUnicode', '', arial_path, uni=True)
                    self.set_font("ArialUnicode", "", 12)
                    st.warning("DejaVu fontları yüklenemedi, Arial Unicode kullanılıyor")
                else:
                    raise Exception("Arial Unicode fontu da bulunamadı")
            except:
                self.set_font("Arial", "", 12)
                st.warning("DejaVu fontları yüklenemedi, standart Arial kullanılıyor (Türkçe karakterler görüntülenmeyebilir)")

    def header(self):
        try:
            self.set_font('DejaVu', 'B', 16)
        except:
            try:
                self.set_font('ArialUnicode', 'B', 16)
            except:
                self.set_font("Arial", "B", 16)
        self.cell(0, 10, 'Finansal Analiz Raporu', 0, 1, 'C')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('DejaVu', '', 8)
        except:
            try:
                self.set_font('ArialUnicode', '', 8)
            except:
                self.set_font("Arial", "", 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

def clear_matplotlib():
    plt.close('all')
    gc.collect()

def write_metrics(pdf):
    try:
        pdf.add_page()
        try:
            pdf.set_font('DejaVu', 'B', 16)
        except:
            pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "FİNANSAL METRİKLER", 0, 1, 'C')
        pdf.ln(10)
        
        # Metrik başlıkları ve değerleri
        metrics = [
            ("F/K Oranı", f"{st.session_state.get('fk', 0):.2f}"),
            ("FD/FAVÖK Oranı", f"{st.session_state.get('fd_divide_favok', 0):.2f}"),
            ("PD/DD Oranı", f"{st.session_state.get('pd_divide_dd', 0):.2f}"),
            ("Cari Oran", f"{st.session_state.get('cariOran', 0):.2f}"),
            ("Asit-Test Oranı", f"{st.session_state.get('asitTestOrani', 0):.2f}"),
            ("Borç/Varlık Oranı", f"{st.session_state.get('borcToplamVarlik', 0):.2f}"),
            ("Net Kâr Marjı", f"{st.session_state.get('netKarMarji', 0):.2%}"),
            ("Aktif Kârlılık Oranı", f"{st.session_state.get('aktifKarlilikOrani', 0):.2%}"),
            ("Özsermaye Kârlılık Oranı", f"{st.session_state.get('ozSermayeKarliligi', 0):.2%}"),
            ("Alacak Devir Hızı", f"{st.session_state.get('alacakDevirHizi', 0):.2f}"),
            ("Stok Devir Hızı", f"{st.session_state.get('stokDevirHizi', 0):.2f}"),
            ("Net Borç", f"{st.session_state.get('netBorc', 0):,.2f} ₺"),
            ("Terminal Değer", f"{st.session_state.get('terminalDegeri', 0):,.2f} ₺"),
            ("Toplam Firma Değeri", f"{st.session_state.get('toplamFirmaDegeri', 0):,.2f} ₺")
        ]
        
        try:
            pdf.set_font('DejaVu', '', 12)
        except:
            pdf.set_font("Arial", "", 12)
            
        for name, value in metrics:
            pdf.cell(0, 10, f"• {name}: {value}", 0, 1)
            pdf.ln(2)
        
        pdf.ln(10)
        return True
    except Exception as e:
        st.error(f"Metrikler yazılırken hata: {str(e)}")
        return False

def create_pdf_report(pdf_path, figures):
    temp_files = []
    try:
        pdf = SimpleFPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Font kontrolü
        if not hasattr(pdf, 'current_font'):
            try:
                pdf.set_font('DejaVu', '', 12)
            except:
                pdf.set_font("Arial", "", 12)
        
        # Önce metrikleri yaz
        if not write_metrics(pdf):
            return False
        
        # Sonra grafikleri ekle
        if not figures:
            st.warning("Eklenecek grafik bulunamadı!")
            return False

        for title, fig in figures:
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    fig.savefig(tmp.name, dpi=120, bbox_inches='tight')
                    temp_files.append(tmp.name)

                plt.close(fig)

                pdf.add_page()
                try:
                    pdf.set_font('DejaVu', 'B', 14)
                except:
                    pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, title, 0, 1, 'C')
                pdf.ln(8)
                pdf.image(tmp.name, x=10, w=190)

            except Exception as e:
                st.error(f"{title} grafiği eklenemedi: {str(e)}")
                continue

        pdf.output(pdf_path)
        return True
    except Exception as e:
        st.error(f"PDF oluşturma hatası: {str(e)}")
        return False
    finally:
        for f in temp_files:
            try:
                os.unlink(f)
            except:
                pass
        plt.close('all')
        gc.collect()


def label_bars(ax, bars, offset=0.2, fmt="{:.2f}"):
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + offset, fmt.format(yval), 
                ha='center', va='bottom', fontsize=10)

def draw_valuation_multiples_chart():
    clear_matplotlib()
    try:
        carpans = ["F/K", "FD/FAVÖK", "PD/DD"]
        degerler = [
            st.session_state.get('fk', 0),
            st.session_state.get('fd_divide_favok', 0),
            st.session_state.get('pd_divide_dd', 0)
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#1f77b4", "#2ca02c", "#ff7f0e"]
        bars = ax.bar(carpans, degerler, color=colors, width=0.6)
        
        ax.set_title("Şirket Değerleme Çarpanları Karşılaştırması", fontsize=14, pad=20)
        ax.set_ylabel("Çarpan Değeri", fontsize=12)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f"{height:.2f}x",
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylim(0, max(degerler) * 1.2)
        plt.xticks(rotation=15, ha='right')
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Çarpan grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_fcf_chart():
    clear_matplotlib()
    try:
        besYillikfcf = st.session_state.get('besYillikfcf', [0]*5)
        yillar = [f"Yıl {i+1}" for i in range(5)]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        line = ax.plot(yillar, besYillikfcf, marker='o', markersize=8, linewidth=2.5,
                      label="FCF Tahmini", color="navy", markerfacecolor='white', markeredgewidth=2)
        
        ax.set_title("5 Yıllık Serbest Nakit Akımı Tahminleri", fontsize=14, pad=20)
        ax.set_xlabel("Yıllar", fontsize=12)
        ax.set_ylabel("FCF (USD)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(fontsize=12, loc='upper left')
        ax.yaxis.set_major_formatter('${x:,.0f}')
        
        for i, val in enumerate(besYillikfcf):
            ax.text(i, val + (max(besYillikfcf)*0.05), f"${val:,.0f}", 
                   ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_ylim(0, max(besYillikfcf) * 1.3)
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"FCF grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_dcf_chart():
    clear_matplotlib()
    try:
        besYillikIndirgemeliDegerler = st.session_state.get('besYillikIndirgemeliDegerler', [0]*5)
        yillar = [f"Yıl {i+1}" for i in range(5)]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(yillar, besYillikIndirgemeliDegerler, color='skyblue')
        
        ax.set_title("5 Yıllık İndirgemeli FCF (NPV)")
        ax.set_ylabel("Bugünkü Değer (USD)")
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height, f"${height:,.0f}",
                    ha='center', va='bottom', fontsize=9)
        
        ax.yaxis.set_major_formatter('${x:,.0f}')
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"DCF grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_terminal_value_chart():
    clear_matplotlib()
    try:
        besYillikIndirgemeliDegerler = st.session_state.get('besYillikIndirgemeliDegerler', [0]*5)
        terminalDegeri = st.session_state.get('terminalDegeri', 0)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.pie([sum(besYillikIndirgemeliDegerler), terminalDegeri],
               labels=["5 Yıllık Nakit Akımları", "Terminal Değer"],
               autopct='%1.1f%%',
               colors=["#FFFB00", "#0C0A7A"],
               startangle=90)
        ax.set_title("Terminal Değerin Toplam Değere Katkısı")
        return fig
    except Exception as e:
        st.error(f"Terminal değer grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_liquidity_chart():
    clear_matplotlib()
    try:
        oranlar = ["Cari Oran", "Asit-Test"]
        degerler = [
            st.session_state.get('cariOran', 0),
            st.session_state.get('asitTestOrani', 0)
        ]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(oranlar, degerler, color=["#4CAF50", "#2196F3"])
        ax.set_title("Likidite Oranları")
        ax.set_ylabel("Oran")
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        label_bars(ax, bars, offset=0.1)
        return fig
    except Exception as e:
        st.error(f"Likidite grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_debt_chart():
    clear_matplotlib()
    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(["Borç / Varlık"], [st.session_state.get('borcToplamVarlik', 0)], color="salmon")
        ax.set_title("Borçluluk Oranı")
        ax.set_ylabel("Oran")
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.02, f"{height:.2f}",
                    ha='center', va='bottom', fontsize=12)
        
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Borç grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_profitability_chart():
    clear_matplotlib()
    try:
        oranlar = ["Net Kâr Marjı", "Aktif Kârlılık", "Özsermaye Kârlılığı"]
        degerler = [
            st.session_state.get('netKarMarji', 0) * 100,
            st.session_state.get('aktifKarlilikOrani', 0) * 100,
            st.session_state.get('ozSermayeKarliligi', 0) * 100
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(oranlar, degerler, color=["#3F51B5", "#009688", "#FFC107"])
        ax.set_title("Kârlılık Oranları Karşılaştırması", pad=20, fontsize=14)
        ax.set_ylabel("Oran (%)", fontsize=12)
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=15, ha='right')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f"{height:.1f}%",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_ylim(0, max(degerler) * 1.2)
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Karlılık grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_activity_chart():
    clear_matplotlib()
    try:
        oranlar = ["Alacak Devir Hızı", "Stok Devir Hızı"]
        degerler = [
            st.session_state.get('alacakDevirHizi', 0),
            st.session_state.get('stokDevirHizi', 0)
        ]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(oranlar, degerler, color=["#7E57C2", "#26C6DA"], width=0.5)
        ax.set_title("Faaliyet Verimliliği Oranları", fontsize=14, pad=20)
        ax.set_ylabel("Devir Hızı (Kat)", fontsize=12)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f"{height:.1f}x",
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        max_value = max(degerler)
        ax.set_ylim(0, max_value * 1.3 if max_value > 0 else 10)
        plt.xticks(rotation=15, ha='right')
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#f8f9fa')
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Faaliyet grafiği oluşturulurken hata: {str(e)}")
        return None

def draw_financial_metrics_chart():
    clear_matplotlib()
    try:
        labels = ['Net Borç', 'Terminal Değer', 'Toplam Şirket Değeri', 'Toplam Firma Değeri']
        values = [
            abs(st.session_state.get('netBorc', 0)),
            st.session_state.get('terminalDegeri', 0),
            st.session_state.get('toplamSirketDegeri', 0),
            st.session_state.get('toplamFirmaDegeri', 0)
        ]
        
        fig, ax = plt.subplots(figsize=(12, 7))
        bars = ax.bar(labels, values, color=['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e'], width=0.6)
        ax.set_title('Temel Finansal Metrikler Karşılaştırması', fontsize=16, pad=20, fontweight='bold')
        ax.set_ylabel('Değer (USD)', fontsize=12)
        ax.set_xlabel('Metrikler', fontsize=12)
        ax.yaxis.set_major_formatter('${x:,.0f}')
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
        for bar in bars:
            height = bar.get_height()
            offset = max(values) * 0.03
            ax.text(bar.get_x() + bar.get_width()/2., height + offset, f"${height:,.0f}",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.xticks(rotation=15, ha='right')
        ax.set_ylim(0, max(values) * 1.15)
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#f8f9fa')
        fig.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Finansal metrik grafiği oluşturulurken hata: {str(e)}")
        return None