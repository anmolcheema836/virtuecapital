import pandas as pd
from fpdf import FPDF
import numpy as np

# 1. Quota Configuration (Standardized Names)
POST_QUOTAS = {
    'Open Merit (General)': {'M': 93, 'W': 40},
    'SC (M&B)': {'M': 21, 'W': 14},
    'SC (R.O.)': {'M': 18, 'W': 14},
    'BC': {'M': 41, 'W': 23},
    'EWS': {'M': 35, 'W': 10},
    'ESM Gen': {'M': 50, 'W': 45},
    'Sports Gen': {'M': 27, 'W': 15}
    # Add others as needed based on the official list
}

TELEGRAM_LINK = "https://t.me/punjabjailwarder"

class MeritPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0, 0, 255)
        self.cell(0, 10, 'CLICK HERE TO JOIN TELEGRAM: @punjabjailwarder', 0, 1, 'C', link=TELEGRAM_LINK)
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'SSSB Punjab Clerk Recruitment 2024', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Category-wise Merit List (Qualified Part-A >= 25)', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()} | Join @punjabjailwarder for more updates', 0, 0, 'C', link=TELEGRAM_LINK)

def clean_data(df):
    """Specific cleaner for the user's Excel format"""
    # 1. Find the Marks columns based on the header positions provided
    # Looking at your printout: Part A is column 13, Part B is column 14
    df = df.iloc[:, [2, 5, 10, 13, 14]].copy()
    df.columns = ['Roll_No', 'Name', 'Gender_Cat_Raw', 'Marks_A', 'Marks_B']

    # 2. Clean Marks (Convert ABS/NA to 0)
    for col in ['Marks_A', 'Marks_B']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('ABS', '0').str.replace('NA', '0'), errors='coerce').fillna(0)

    # 3. Split Gender and Category
    def extract_gender(val):
        val = str(val)
        if 'Female' in val: return 'W'
        return 'M'

    def extract_cat(val):
        val = str(val).lower()
        if 'm & b' in val: return 'SC (M&B)'
        if 'ramdasia' in val or 'r & o' in val: return 'SC (R.O.)'
        if 'b.c' in val: return 'BC'
        if 'ews' in val: return 'EWS'
        if 'esm' in val: return 'ESM Gen'
        if 'sports' in val: return 'Sports Gen'
        return 'General'

    df['Gender'] = df['Gender_Cat_Raw'].apply(extract_gender)
    df['Category'] = df['Gender_Cat_Raw'].apply(extract_cat)
    
    return df

def generate_merit_list():
    try:
        # Load data (skip header rows if they are nested)
        raw_df = pd.read_excel('clerk.xlsx')
        df = clean_data(raw_df)

        # Filter Qualified
        qualified_df = df[df['Marks_A'] >= 25].copy()
        qualified_df = qualified_df.sort_values(by=['Marks_B', 'Marks_A'], ascending=False)

        selected_ids = []
        final_results = {}

        # --- SELECTION LOGIC ---
        
        # 1. OPEN MERIT (General)
        open_w_limit = POST_QUOTAS['Open Merit (General)']['W']
        open_m_limit = POST_QUOTAS['Open Merit (General)']['M']
        
        open_w = qualified_df[qualified_df['Gender'] == 'W'].head(open_w_limit)
        selected_ids.extend(open_w['Roll_No'].tolist())
        
        remaining = qualified_df[~qualified_df['Roll_No'].isin(selected_ids)]
        open_gen = remaining.head(open_m_limit)
        selected_ids.extend(open_gen['Roll_No'].tolist())
        
        final_results['Open Merit (General)'] = pd.concat([open_w, open_gen])

        # 2. RESERVED CATEGORIES
        for cat_name, quota in POST_QUOTAS.items():
            if cat_name == 'Open Merit (General)': continue
            
            cat_pool = qualified_df[(qualified_df['Category'] == cat_name) & (~qualified_df['Roll_No'].isin(selected_ids))]
            
            w_sel = cat_pool[cat_pool['Gender'] == 'W'].head(quota['W'])
            selected_ids.extend(w_sel['Roll_No'].tolist())
            
            m_sel = cat_pool[(cat_pool['Gender'] == 'M') & (~cat_pool['Roll_No'].isin(selected_ids))].head(quota['M'])
            selected_ids.extend(m_sel['Roll_No'].tolist())
            
            final_results[cat_name] = pd.concat([w_sel, m_sel])

        # --- PDF GENERATION ---
        pdf = MeritPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for cat, data in final_results.items():
            if data.empty: continue
            pdf.add_page()
            pdf.set_font('Arial', 'B', 12)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(0, 10, f" Category: {cat} ", 1, 1, 'L', True)
            
            # Header
            pdf.set_font('Arial', 'B', 10)
            widths = [15, 25, 85, 20, 20, 25]
            cols = ['Rank', 'Roll No', 'Name', 'Gender', 'Part A', 'Part B']
            for i in range(len(cols)):
                pdf.cell(widths[i], 10, cols[i], 1, 0, 'C')
            pdf.ln()

            # Data
            pdf.set_font('Arial', '', 9)
            for idx, row in data.reset_index(drop=True).iterrows():
                pdf.cell(widths[0], 8, str(idx+1), 1, 0, 'C')
                pdf.cell(widths[1], 8, str(row['Roll_No']), 1, 0, 'C')
                pdf.cell(widths[2], 8, str(row['Name'])[:45], 1, 0, 'L')
                pdf.cell(widths[3], 8, str(row['Gender']), 1, 0, 'C')
                pdf.cell(widths[4], 8, str(row['Marks_A']), 1, 0, 'C')
                pdf.cell(widths[5], 8, str(row['Marks_B']), 1, 1, 'C')

        pdf.output('Punjab_Clerk_Merit_List.pdf')
        print("PDF Success: Created 'Punjab_Clerk_Merit_List.pdf'")

    except Exception as e:
        print(f"Error logic: {e}")

if __name__ == "__main__":
    generate_merit_list()