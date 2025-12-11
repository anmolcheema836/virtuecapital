import pandas as pd
from fpdf import FPDF
import os

# --- CONFIGURATION ---
RESULT_FILE = "warder.xlsx"
MARKS_FILE = "numbersofwarder.xlsx"
OUTPUT_FILE = "Final_Selection_List_175.pdf"
TELEGRAM_LINK = "https://t.me/punjabjailwarder"

# --- SEAT DISTRIBUTION RULES ---
SEAT_QUOTAS = [
    # (Display Name, Count, Internal Category Match Keywords)
    # The 'Open' category is handled specially in code (Top 75 regardless of cat)
    ("Open / General (Merit)", 75, ["ANY"]), 
    
    # Reserved Categories (Applied to remaining candidates)
    ("Economic Weaker Section", 17, ["ews"]),
    ("Scheduled Caste (M&B)", 18, ["s.c (m", "sc (m", "mazhbi"]),
    ("Scheduled Caste (R&O)", 17, ["s.c (r", "sc (r", "ramdasia"]),
    ("Backward Class", 18, ["b.c", "bc", "backward"]),
    ("Ex-Serviceman (General)", 13, ["esm gen", "esm (gen"]),
    ("Ex-Serviceman (SC M&B)", 4, ["esm sc (m", "esm sc(m"]),
    ("Ex-Serviceman (SC R&O)", 3, ["esm sc (r", "esm sc(r"]),
    ("Ex-Serviceman (BC)", 3, ["esm bc", "esm (bc"]),
    ("Sports (General)", 3, ["sports gen", "sports (gen"]),
    ("Sports (SC M&B)", 1, ["sports (sc-m", "sports sc (m"]),
    ("Sports (SC R&O)", 1, ["sports (sc-r", "sports sc (r"]),
    ("Freedom Fighter", 2, ["freedom"]),
]

class PDF(FPDF):
    def header(self):
        # Top Watermark
        self.set_font('Arial', 'I', 10)
        self.set_text_color(0, 102, 204)
        self.cell(0, 6, f'Join Telegram: {TELEGRAM_LINK}', 0, 1, 'C', link=TELEGRAM_LINK)
        
        # Title
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'FINAL SELECTION LIST (Top 175 Candidates)', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, 'Post of Warder (Advt No. 08 of 2024)', 0, 1, 'C')
        self.ln(2)
        
        # Table Header
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(220, 220, 220)
        
        # Widths: Sr, Roll, Name, Father, Orig_Cat, Marks, Selection_Cat
        self.widths = [10, 18, 55, 55, 45, 15, 75]
        headers = ["Sr", "Roll No", "Candidate Name", "Father's Name", "Original Category", "Marks", "Selected Under Category"]
        
        for i, text in enumerate(headers):
            self.cell(self.widths[i], 10, text, border=1, align='C', fill=True)
        self.ln()

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, f'Join for Updates: {TELEGRAM_LINK}', 0, 1, 'C', link=TELEGRAM_LINK)
        self.set_y(-15)
        self.set_text_color(128)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')

def find_header_row_fuzzy(df, k1, k2):
    for i, row in df.iterrows():
        vals = [str(v).lower() for v in row.values]
        if any(k1.lower() in x for x in vals) and any(k2.lower() in x for x in vals):
            return i
    return -1

def clean_roll_no(val):
    try:
        return str(int(float(val))).strip()
    except:
        return str(val).strip()

def normalize_category(raw_cat, quota_list):
    """
    Matches the raw Excel category string to one of our Selection Categories.
    This ensures 'S.C (M & B)' matches the 'Scheduled Caste (M&B)' bucket.
    """
    raw = str(raw_cat).lower().strip()
    
    # Check strict buckets (skip Open as that is automatic)
    for display_name, count, keywords in quota_list[1:]: 
        for k in keywords:
            if k in raw:
                return display_name
    
    # Fallback for General if not matched above
    if 'gen' in raw and 'ews' not in raw and 'esm' not in raw and 'sports' not in raw:
        return "General"
        
    return "Other"

def process_selection_list():
    # 1. READ & MERGE DATA (Same logic as before)
    print("Reading files...")
    if not os.path.exists(RESULT_FILE) or not os.path.exists(MARKS_FILE):
        print("Error: Files not found.")
        return

    try:
        # Read Result
        r_raw = pd.read_excel(RESULT_FILE, header=None)
        r_idx = find_header_row_fuzzy(r_raw, "Roll", "Result")
        df_res = pd.read_excel(RESULT_FILE, header=r_idx)
        df_res.columns = df_res.columns.str.strip()
        
        # Read Marks
        m_raw = pd.read_excel(MARKS_FILE, header=None)
        m_idx = find_header_row_fuzzy(m_raw, "Roll", "MKS")
        df_mks = pd.read_excel(MARKS_FILE, header=m_idx)
        df_mks.columns = df_mks.columns.str.strip()
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Identify Columns
    res_roll = next(c for c in df_res.columns if "Roll" in c)
    res_cat = next(c for c in df_res.columns if "Category" in c)
    res_name = next(c for c in df_res.columns if "Candidate" in c)
    res_father = next(c for c in df_res.columns if "Father" in c)
    res_status = next(c for c in df_res.columns if "Result" in c)
    
    mks_roll = next(c for c in df_mks.columns if "Roll" in c)
    mks_val = next(c for c in df_mks.columns if "MKS" in c)

    # Filter Qualified
    df_res[res_status] = df_res[res_status].astype(str)
    qualified = df_res[
        (df_res[res_status].str.contains("Qualified", case=False)) & 
        (~df_res[res_status].str.contains("Not", case=False))
    ].copy()

    # Merge Marks
    qualified['Match_Roll'] = qualified[res_roll].apply(clean_roll_no)
    df_mks['Match_Roll'] = df_mks[mks_roll].apply(clean_roll_no)
    
    merged = pd.merge(qualified, df_mks[['Match_Roll', mks_val]], on='Match_Roll', how='left')
    merged[mks_val] = merged[mks_val].fillna(0)
    
    # Normalize Category for filtering
    merged['Norm_Cat'] = merged[res_cat].apply(lambda x: normalize_category(x, SEAT_QUOTAS))

    # --- THE SELECTION ALGORITHM ---
    print("Running Selection Algorithm...")
    
    # 1. Sort EVERYONE by Marks (Desc)
    # We sort by Marks, then Name to handle ties deterministically
    merged.sort_values(by=[mks_val, res_name], ascending=[False, True], inplace=True)
    
    final_selection = []
    selected_indices = []

    # 2. FILL OPEN CATEGORY (Top 75)
    open_quota = SEAT_QUOTAS[0][1] # 75
    
    # Take top 75 available candidates
    open_candidates = merged.iloc[:open_quota].copy()
    
    for idx, row in open_candidates.iterrows():
        row['Allocated_Category'] = "Open / General (Merit)"
        final_selection.append(row)
        selected_indices.append(idx)
        
    print(f"Filled 75 Open Merit seats (Cutoff: {open_candidates.iloc[-1][mks_val]})")

    # 3. FILL RESERVED CATEGORIES
    # Create a pool of remaining candidates
    remaining_pool = merged.drop(selected_indices)

    # Loop through the rest of the quotas
    for display_name, count, keywords in SEAT_QUOTAS[1:]:
        # Filter pool for this specific category
        # We match based on the 'Norm_Cat' we created earlier
        eligible = remaining_pool[remaining_pool['Norm_Cat'] == display_name]
        
        # Take the top 'count' from this filtered list
        selected = eligible.head(count).copy()
        
        print(f"Filled {len(selected)}/{count} seats for {display_name}")
        
        for idx, row in selected.iterrows():
            row['Allocated_Category'] = display_name
            final_selection.append(row)
            # Remove from pool so they aren't picked again (though unlikely given logic)
            remaining_pool = remaining_pool.drop(idx)

    # --- CREATE DATAFRAME FOR PDF ---
    final_df = pd.DataFrame(final_selection)
    
    # Add Sorting Order for PDF presentation
    # 1. Order by the SEAT_QUOTAS list (Open first, then EWS, then SC...)
    # 2. Then by Marks
    cat_order = {item[0]: i for i, item in enumerate(SEAT_QUOTAS)}
    final_df['Sort_Order'] = final_df['Allocated_Category'].map(cat_order)
    
    final_df.sort_values(by=['Sort_Order', mks_val], ascending=[True, False], inplace=True)
    
    # Add Final Sr No (1 to 175)
    final_df.reset_index(drop=True, inplace=True)
    final_df.index += 1
    
    # --- GENERATE PDF ---
    print(f"Generating PDF with {len(final_df)} candidates...")
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('Arial', '', 8)

    widths = [10, 18, 55, 55, 45, 15, 75]
    previous_alloc = ""

    for index, row in final_df.iterrows():
        try:
            current_alloc = row['Allocated_Category']
            
            # Section Header
            if current_alloc != previous_alloc:
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(0, 0, 0) # Black bar
                pdf.set_text_color(255, 255, 255) # White text
                
                # Count how many in this category
                count_in_cat = len(final_df[final_df['Allocated_Category'] == current_alloc])
                
                header_text = f"{current_alloc} (Selected: {count_in_cat})"
                pdf.cell(sum(widths), 8, header_text, border=1, align='L', fill=True)
                pdf.ln()
                
                # Reset styles
                pdf.set_font('Arial', '', 8)
                pdf.set_text_color(0, 0, 0)
                previous_alloc = current_alloc

            # Prepare Data
            sr = str(index)
            roll = str(row[res_roll])
            name = str(row[res_name])
            father = str(row[res_father])
            orig_cat = str(row[res_cat]) # Use original detailed category name
            mks = f"{float(row[mks_val]):.2f}"
            sel_cat = str(row['Allocated_Category'])

            data = [sr, roll, name, father, orig_cat, mks, sel_cat]
            
            # Check Page Break
            if pdf.get_y() > 180:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(0, 0, 0)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(sum(widths), 8, f"{current_alloc} (Cont.)", border=1, align='L', fill=True)
                pdf.ln()
                pdf.set_font('Arial', '', 8)
                pdf.set_text_color(0, 0, 0)

            # Draw Row
            max_y = pdf.get_y()
            for i, txt in enumerate(data):
                txt = txt.replace('\n', ' ')[:45]
                pdf.cell(widths[i], 8, txt, border=1, align='L')
            pdf.ln()

        except Exception as e:
            print(f"Row Error: {e}")

    pdf.output(OUTPUT_FILE)
    print(f"SUCCESS! Created {OUTPUT_FILE}")

if __name__ == "__main__":
    process_selection_list()