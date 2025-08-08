import pandas as pd
from docx import Document
import tempfile
import os
import io
from typing import List, Union, Optional  # Tip tanımlamaları için
import warnings  # Uyarıları yönetmek için
from pathlib import Path 

def extract_tables_from_docx(uploaded_file):
    file_bytes = uploaded_file.read()  

    with tempfile.TemporaryDirectory() as temp_dir:
        docx_path = os.path.join(temp_dir, "input.docx")
        with open(docx_path, "wb") as f:
            f.write(file_bytes)

        doc = Document(docx_path)

        tables = []
        for table in doc.tables:
            data = []
            keys = None

            for r_idx, row in enumerate(table.rows):
                row_data = [cell.text.strip() for cell in row.cells]
                if r_idx == 0:
                    keys = row_data
                else:
                    data.append(row_data)

            if keys:
                df = pd.DataFrame(data, columns=keys)
            else:
                df = pd.DataFrame(data)

            tables.append(df)

        return tables
    
def extract_tables_from_excel(excel_file):
    """
    Excel dosyasındaki tüm sayfalardaki tabloları çıkarır
    
    Parametreler:
        excel_file: Yüklenen Excel dosyası (Streamlit file_uploader objesi)
    
    Dönüş:
        Tabloların listesi (DataFrame'ler)
    """
    try:
        # Excel dosyasını oku
        excel_data = pd.ExcelFile(io.BytesIO(excel_file.read()))
        tables = []
        
        # Her sayfayı işle
        for sheet_name in excel_data.sheet_names:
            df = pd.read_excel(excel_data, sheet_name=sheet_name)
            
            # Boş olmayan ve geçerli sütun isimleri olan tabloları ekle
            if not df.empty and not all(col.startswith('Unnamed') for col in df.columns):
                # Sayfa adını dataframe'e ek özellik olarak kaydet
                df.attrs['sheet_name'] = sheet_name  
                tables.append(df)
                
        return tables
        
    except Exception as e:
        print(f"Excel dosyası işleme hatası: {str(e)}")
        return []
    

