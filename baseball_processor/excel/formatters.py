import logging
import pandas as pd
from xlsxwriter.utility import xl_col_to_name

# Configuration constants
DEFAULT_ROW_HEIGHT = 25
HEADER_ROW_HEIGHT = 28
MAX_COLUMN_WIDTH = 50
MIN_COLUMN_WIDTH = 8
CONTENT_PADDING = 3

# Column format configuration
COLUMN_FORMATS = {
    'baseball_3dec': ["AVG", "OBP", "SLG", "OPS", "WHIP"],
    'baseball_2dec': ["ERA"],
    'baseball_1dec': ["IP", "Runs/Game", "Runs Allowed/Game", "Run Diff/Game", "HRs/Game", "Hits/Game"],
    'dates': ["Date", "First Visit", "Last Visit", "First Game", "Last Game"],
    'times': ["Game Length"],
    'attendance': ["Attendance", "High Attendance", "Low Attendance", "Avg Attendance"],
    'percentages': ["Win%"],
    'center_text': ["Team", "Opponent", "Home/Away", "Position", "Decision", "Inning", 
                   "Half", "Venue", "Stadium", "Most Common Start","Orioles Record", 
                   "Home Team Record", "1-Run Games", "Blowouts (5+)", "Extra Innings", "Walk-offs"],
    'float_rates': ["Runs/Game", "Runs Allowed/Game", "Run Diff/Game", "HRs/Game", 
                   "Hits/Game", "Ks/Game", "HRs per Game", "Hits per Game", 
                   "Strikeouts per Game", "Avg Duration"],
    'integers': ["G", "GS", "W", "L", "SV", "AB", "PA", "H", "R", "RBI", "HR", 
                "2B", "3B", "SB", "CS", "HBP", "BB", "SO", "TB", "XBH", "GIDP",
                "Games", "Wins", "Losses", "Runs Scored", "Runs Allowed", 
                "Run Differential", "Team Hits", "Team HRs", "Team SBs",
                "Walks Taken", "Strikeouts By", "Strikeouts For", "Walks Allowed",
                "Home Runs Seen", "Hits Seen", "Strikeouts Seen", "Teams Seen",
                "Longest Win Streak", "Longest Loss Streak", "Total", "BF",
                "Pitches", "Swinging K", "Looking K", "ER", "Value",
                "H_P", "R_P", "BB_P", "SO_P", "Year Inducted", "Games Seen", 
                "Strikeouts by O's", "Hits", "Home Runs Hit", "HR Count", "Outs",
                "HP", "1B", "LF", "RF"],
    'narrow_stats': ["G", "GS", "W", "L", "SV"],
    'gameids': ["GameIDs"],
    'gameid': ["GameID", "Game ID"],
    'long_text': ["Detail", "Description", "Plays"],
    'summary_detail': ["Detail"],
    'summary_score': ["Score"],
    'summary_record': ["Record"]
}

def get_column_format_type(col_name):
    """Determine format type for a column."""
    for format_type, columns in COLUMN_FORMATS.items():
        if col_name in columns:
            return format_type
    
    # Temperature columns (dynamic check)
    if "Temp" in col_name:
        return 'temperature'
        
    return 'default'

def create_format_pair(workbook, colors, num_format=None, align='left', extra_props=None):
    """Create even/odd format pair with consistent styling."""
    base_props = {
        'border': 1,
        'align': align
    }
    
    if num_format:
        base_props['num_format'] = num_format
    
    if extra_props:
        base_props.update(extra_props)
    
    even_props = base_props.copy()
    even_props['bg_color'] = colors['white']
    
    odd_props = base_props.copy()
    odd_props['bg_color'] = colors['light_gray']
    
    return (workbook.add_format(even_props), workbook.add_format(odd_props))

def safe_temperature_format(temp_value):
    """Safely format temperature with degree symbol fallback."""
    try:
        return f"{temp_value}°F"
    except (UnicodeEncodeError, UnicodeDecodeError):
        return f"{temp_value} deg F"

def calculate_optimal_width(content_width, format_type, col_name):
    """Calculate optimal column width based on format type."""
    if format_type == 'narrow_stats':
        return min(max(content_width, 4), 6)
    elif format_type == 'integers' and col_name in ["AB", "H", "R", "RBI", "HR", "2B", "HBP", "3B", "BB", "SO", "H_P", "R_P", "ER", "BB_P", "SO_P"]:
        return min(max(content_width, 4), 7)
    elif format_type == 'baseball_1dec': 
        return max(content_width, 6)
    elif format_type == 'long_text':
        return min(max(content_width, 25), 50)
    elif col_name == "Plays":
        return content_width
    elif format_type == 'gameids':
        return content_width
    elif format_type == 'gameid':
        return 15 if col_name == "GameID" else content_width
    else:
        return min(max(content_width, 8), 35)

def clean_content_for_measurement(text):
    """Clean content to get accurate character count."""
    import unicodedata
    import re
    
    text = str(text) if text is not None else ""
    text = text.replace('\xa0', ' ').replace('\u2000', ' ').replace('\u2001', ' ')
    text = text.replace('\u2002', ' ').replace('\u2003', ' ').replace('\u2009', ' ')
    text = unicodedata.normalize('NFKD', text).strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def create_workbook_theme(workbook):
    """Create a consistent visual theme for the entire workbook."""
    
    # Color palette - professional baseball theme
    colors = {
        'primary_blue': '#1B365D',      # Deep navy blue
        'secondary_blue': '#4A90A4',    # Medium blue  
        'light_blue': '#E8F4F8',       # Very light blue
        'accent_green': '#2E7D32',      # Forest green
        'light_green': '#E8F5E8',      # Very light green
        'warning_orange': '#F57C00',    # Orange
        'light_orange': '#FFF3E0',     # Very light orange
        'error_red': '#C62828',        # Red
        'light_red': '#FFEBEE',        # Very light red
        'neutral_gray': '#757575',     # Medium gray
        'light_gray': '#F5F5F5',       # Very light gray
        'white': '#FFFFFF'
    }
    
    # Header formats
    formats = {
        'main_header': workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': colors['primary_blue'],
            'font_color': colors['white'],
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': colors['neutral_gray']
        }),
        
        'sub_header': workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': colors['secondary_blue'],
            'font_color': colors['white'],
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        }),
        
        'section_header': workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': colors['light_blue'],
            'font_color': colors['primary_blue'],
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        }),
        
        # Data formats with subtle backgrounds
        'data_even': workbook.add_format({
            'bg_color': colors['white'],
            'border': 1,
            'border_color': colors['light_gray']
        }),
        
        'data_odd': workbook.add_format({
            'bg_color': colors['light_gray'],
            'border': 1,
            'border_color': colors['neutral_gray']
        }),
        
        # Number formats with styling
        'batting_avg': workbook.add_format({
            'num_format': '0.000',
            'align': 'center',
            'bg_color': colors['light_green'],
            'border': 1
        }),
        
        'era_format': workbook.add_format({
            'num_format': '0.00',
            'align': 'center',
            'bg_color': colors['light_orange'],
            'border': 1
        }),
        
        'percentage': workbook.add_format({
            'num_format': '0.0%',
            'align': 'center',
            'bg_color': colors['light_blue'],
            'border': 1
        }),
        
        'currency': workbook.add_format({
            'num_format': '#,##0',
            'align': 'right',
            'border': 1
        }),
        
        'date_format': workbook.add_format({
            'num_format': 'mm/dd/yyyy',
            'align': 'center',
            'bg_color': colors['light_blue'],
            'border': 1
        }),
        
        'stat_highlight': workbook.add_format({
            'bold': True,
            'bg_color': colors['accent_green'],
            'font_color': colors['white'],
            'align': 'center',
            'border': 1
        })
    }
    
    return formats, colors

def format_sheet_comprehensively(writer, df, sheet_name, workbook, colors, sheet_type="default", exclude_cols=None):
    """
    Comprehensive sheet formatting that handles all cells with proper shading and number storage.
    """
    if sheet_name not in writer.sheets or df.empty:
        return
        
    worksheet = writer.sheets[sheet_name]
    exclude_cols = exclude_cols or []
    
    # Create all the formats we need efficiently
    formats = {
        'header': workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': colors['primary_blue'],
            'font_color': colors['white'],
            'align': 'center',
            'border': 1
        })
    }

    # Create format pairs efficiently
    text_even, text_odd = create_format_pair(workbook, colors, align='left')
    number_even, number_odd = create_format_pair(workbook, colors, num_format='0', align='center')
    float_even, float_odd = create_format_pair(workbook, colors, num_format='0.00', align='center')
    avg_even, avg_odd = create_format_pair(workbook, colors, num_format='0.000', align='center')
    era_even, era_odd = create_format_pair(workbook, colors, num_format='0.00', align='center')
    ip_even, ip_odd = create_format_pair(workbook, colors, num_format='0.0', align='center')
    whip_even, whip_odd = create_format_pair(workbook, colors, num_format='0.000', align='center')
    date_even, date_odd = create_format_pair(workbook, colors, num_format='mm/dd/yyyy', align='center')
    attendance_even, attendance_odd = create_format_pair(workbook, colors, num_format='#,##0', align='right')
    percentage_even, percentage_odd = create_format_pair(workbook, colors, num_format='0.0%', align='center')
    time_even, time_odd = create_format_pair(workbook, colors, num_format='h:mm', align='center')
    center_even, center_odd = create_format_pair(workbook, colors, align='center')

    # Add to formats dict
    formats.update({
        'text_even': text_even, 'text_odd': text_odd,
        'number_even': number_even, 'number_odd': number_odd,
        'float_even': float_even, 'float_odd': float_odd,
        'avg_even': avg_even, 'avg_odd': avg_odd,
        'era_even': era_even, 'era_odd': era_odd,
        'ip_even': ip_even, 'ip_odd': ip_odd,
        'whip_even': whip_even, 'whip_odd': whip_odd,
        'date_even': date_even, 'date_odd': date_odd,
        'attendance_even': attendance_even, 'attendance_odd': attendance_odd,
        'percentage_even': percentage_even, 'percentage_odd': percentage_odd,
        'time_even': time_even, 'time_odd': time_odd,
        'center_even': center_even, 'center_odd': center_odd
    })
    
    # Set column widths based on actual content
    for col_idx, col_name in enumerate(df.columns):
        if col_name in exclude_cols:
            continue
            
        # Calculate width based on actual content
        header_width = len(str(col_name)) + 2
        content_width = header_width
        
        if not df.empty and col_name in df.columns:
            try:
                # Sample only first 50 rows for performance, and handle NaN values
                sample_data = df[col_name].head(50).fillna('').apply(clean_content_for_measurement)
                if not sample_data.empty:
                    # Use 90th percentile instead of max to avoid outliers
                    content_length = max(sample_data.str.len().quantile(0.9), sample_data.str.len().max())
                    content_width = max(header_width, content_length + CONTENT_PADDING)
                else:
                    content_width = header_width
            except (ValueError, TypeError, AttributeError):
                content_width = header_width
        
        # Calculate optimal width based on column type
        format_type = get_column_format_type(col_name)
        optimal_width = calculate_optimal_width(content_width, format_type, col_name)
        
        worksheet.set_column(col_idx, col_idx, optimal_width)
    
    # Write headers
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(0, col_idx, col_name, formats['header'])
    worksheet.set_row(0, DEFAULT_ROW_HEIGHT)

    # Write data with proper formatting
    for row_idx in range(len(df)):
        excel_row = row_idx + 1  # Excel is 1-based, skip header
        is_even_row = excel_row % 2 == 1
        
        for col_idx, col_name in enumerate(df.columns):
            if col_name in exclude_cols:
                continue
                
            value = df.iloc[row_idx, col_idx]
            
            # Determine format based on column type
            format_type = get_column_format_type(col_name)
            format_key, write_as_number = _determine_cell_format(
                format_type, col_name, value, is_even_row, sheet_type
            )
            
            # Handle special date formatting
            if format_type == 'dates':
                if hasattr(value, 'strftime'):
                    worksheet.write_datetime(excel_row, col_idx, value, formats[format_key])
                elif pd.notna(value):
                    worksheet.write_string(excel_row, col_idx, str(value), formats[format_key])
                else:
                    worksheet.write_string(excel_row, col_idx, "", formats[format_key])
                continue
            
            # Handle temperature formatting
            if format_type == 'temperature' and pd.notna(value):
                if isinstance(value, str) and "°F" in str(value):
                    temp_num = value.replace("°F", "").strip()
                    try:
                        value = safe_temperature_format(int(temp_num))
                    except (ValueError, TypeError):
                        value = str(value)
            
            # Write the cell
            if write_as_number:
                _write_numeric_cell(worksheet, excel_row, col_idx, value, formats[format_key])
            else:
                _write_text_cell(worksheet, excel_row, col_idx, value, formats[format_key])
    
    # Add hyperlinks for Player ID columns
    _add_player_id_hyperlinks(worksheet, df, workbook, colors)
    
    # Add text wrapping for long text columns
    _apply_text_wrapping(worksheet, df, workbook)
    
    # Freeze header row
    worksheet.freeze_panes(1, 0)

def _determine_cell_format(format_type, col_name, value, is_even_row, sheet_type):
    """Determine the appropriate format key and whether to write as number."""
    write_as_number = False
    
    if format_type == 'baseball_3dec':
        format_key = "avg_even" if is_even_row else "avg_odd"
        write_as_number = True
    elif format_type == 'baseball_2dec':
        format_key = "era_even" if is_even_row else "era_odd"
        write_as_number = True
    elif format_type == 'baseball_1dec':
        format_key = "ip_even" if is_even_row else "ip_odd"
        write_as_number = True
    elif format_type == 'dates':
        format_key = "date_even" if is_even_row else "date_odd"
    elif format_type == 'times':
        format_key = "time_even" if is_even_row else "time_odd"
        write_as_number = True
    elif format_type == 'attendance':
        format_key = "attendance_even" if is_even_row else "attendance_odd"
        write_as_number = True
    elif format_type == 'percentages':
        format_key = "percentage_even" if is_even_row else "percentage_odd"
        write_as_number = True
    elif format_type == 'center_text':
        format_key = "center_even" if is_even_row else "center_odd"
    elif format_type == 'float_rates':
        format_key = "float_even" if is_even_row else "float_odd"
        write_as_number = True
    elif format_type == 'temperature':
        format_key = "center_even" if is_even_row else "center_odd"
    elif format_type == 'integers':
        format_key = "number_even" if is_even_row else "number_odd"
        write_as_number = True
    elif sheet_type == "summary" and col_name == "Value":
        # Special handling for Summary Stats Value column
        if isinstance(value, (int, float)):
            format_key = "number_even" if is_even_row else "number_odd"
            write_as_number = True
        elif isinstance(value, str) and value.replace('.', '').replace('-', '').replace(',', '').isdigit():
            format_key = "number_even" if is_even_row else "number_odd"
            write_as_number = True
        else:
            format_key = "center_even" if is_even_row else "center_odd"
    elif isinstance(value, (int, float)) or (isinstance(value, str) and str(value).replace('.','').replace('-','').isdigit()):
        # Numeric data detection
        if isinstance(value, float) or (isinstance(value, str) and '.' in str(value)):
            format_key = "float_even" if is_even_row else "float_odd"
        else:
            format_key = "number_even" if is_even_row else "number_odd"
        write_as_number = True
    else:
        # Text data
        format_key = "text_even" if is_even_row else "text_odd"
    
    return format_key, write_as_number

def _write_numeric_cell(worksheet, excel_row, col_idx, value, format_obj):
    """Write a numeric cell with proper type conversion."""
    try:
        if isinstance(value, str):
            # Enhanced string to number conversion
            clean_value = value.strip().replace(',', '')  # Remove commas
            if clean_value.endswith('%'):
                numeric_value = float(clean_value.rstrip('%')) / 100
            elif '.' in clean_value and clean_value.replace('.', '').replace('-', '').isdigit():
                numeric_value = float(clean_value)
            elif clean_value.replace('-', '').isdigit():
                numeric_value = int(clean_value)
            else:
                numeric_value = float(clean_value)
        else:
            numeric_value = value
        
        if pd.notna(numeric_value) and numeric_value != '':
            worksheet.write_number(excel_row, col_idx, float(numeric_value), format_obj)
        else:
            worksheet.write_string(excel_row, col_idx, "", format_obj)
    except (ValueError, TypeError):
        # If conversion fails, write as string
        if pd.notna(value) and value != '':
            worksheet.write_string(excel_row, col_idx, str(value), format_obj)
        else:
            worksheet.write_string(excel_row, col_idx, "", format_obj)

def _write_text_cell(worksheet, excel_row, col_idx, value, format_obj):
    """Write a text cell."""
    if pd.notna(value):
        worksheet.write_string(excel_row, col_idx, str(value), format_obj)
    else:
        worksheet.write_string(excel_row, col_idx, "", format_obj)

def _add_player_id_hyperlinks(worksheet, df, workbook, colors):
    """Add hyperlinks for Player ID columns."""
    for id_col in ["Player ID", "PlayerID"]:
        if id_col in df.columns:
            player_id_col = df.columns.get_loc(id_col)
            for row_idx in range(len(df)):
                excel_row = row_idx + 1
                player_id = df.iloc[row_idx][id_col]
                if player_id and player_id != "UNKNOWN":
                    first_letter = player_id[0].lower()
                    url = f"https://www.baseball-reference.com/players/{first_letter}/{player_id}.shtml"
                    
                    is_even_row = excel_row % 2 == 1
                    bg_color = colors['white'] if is_even_row else colors['light_gray']
                    hyperlink_format = workbook.add_format({
                        'font_color': 'blue',
                        'underline': True,
                        'align': 'center',
                        'border': 1,
                        'bg_color': bg_color
                    })
                    worksheet.write_url(excel_row, player_id_col, url, hyperlink_format, string=player_id)

def _apply_text_wrapping(worksheet, df, workbook):
    """Apply text wrapping for long text columns."""
    for col_idx, col_name in enumerate(df.columns):
        if col_name in ["Detail", "Description", "Plays"]:
            wrap_format = workbook.add_format({
                'text_wrap': True, 
                'valign': 'top',
                'align': 'left',
                'border': 1
            })
            worksheet.set_column(col_idx, col_idx, None, wrap_format)

def format_milestone_sheet_specifically(writer, df, sheet_name, workbook, colors, exclude_cols=None):
    """
    Milestone-specific formatting that handles the unique column requirements.
    """
    if sheet_name not in writer.sheets or df.empty:
        return
        
    worksheet = writer.sheets[sheet_name]
    exclude_cols = exclude_cols or []
    
    # Determine milestone category color
    milestone_type = sheet_name.lower()
    if any(word in milestone_type for word in ['hit', 'rbi', 'hr', 'cycle', 'grand']):
        category_color = colors['accent_green']
    elif any(word in milestone_type for word in ['strikeout', 'pitch', 'quality', 'inning']):
        category_color = colors['primary_blue'] 
    else:
        category_color = colors.get('warning_orange', '#F57C00')
    
    # Create milestone-specific formats
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bg_color': category_color,
        'font_color': colors['white'],
        'align': 'center',
        'valign': 'vcenter',
        'border': 2,
        'border_color': colors.get('neutral_gray', '#757575')
    })
    
    # Create alternating row formats using the helper function
    even_text, odd_text = create_format_pair(workbook, colors, align='left')
    even_center, odd_center = create_format_pair(workbook, colors, align='center')
    even_number, odd_number = create_format_pair(workbook, colors, num_format='0', align='center')
    even_date, odd_date = create_format_pair(workbook, colors, num_format='mm/dd/yyyy', align='center')
    even_wrap, odd_wrap = create_format_pair(workbook, colors, align='left', extra_props={'text_wrap': True, 'valign': 'top'})
    
    # Basic wrap format for column setting (no background color)
    basic_wrap = workbook.add_format({
        'text_wrap': True,
        'valign': 'top'
    })
    
    # Write headers first
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(0, col_idx, col_name, header_format)
    worksheet.set_row(0, DEFAULT_ROW_HEIGHT)
    
    # Set column widths based on milestone content
    milestone_widths = {
        "Date": 12, "Player": 20, "Team": 8, "Opponent": 12, 
        "Score": 20, "Home/Away": 12, "Inning": 15, "Pitcher": 18, 
        "Replaced Player": 18, "Swinging K": 12, "Looking K": 12,
        "BF": 6, "Pitches": 10, "GameID": 14,
        "Batters Struck Out": 45
    }
    
    for col_idx, col_name in enumerate(df.columns):
        if col_name in exclude_cols:
            continue
            
        # Handle special width columns first
        if col_name in ["Plays", "Players", "Pitchers"]:
            if col_name == "Plays":
                worksheet.set_column(col_idx, col_idx, 50, basic_wrap)   # Handles 85 chars + padding
            elif col_name == "Players":
                worksheet.set_column(col_idx, col_idx, 35, basic_wrap) 
            else:
                worksheet.set_column(col_idx, col_idx, 25, basic_wrap)   # Handles 38 chars + padding
        elif col_name in ["Detail"]:
            worksheet.set_column(col_idx, col_idx, 50, basic_wrap)
        elif col_name in milestone_widths:
            width = milestone_widths[col_name]
            worksheet.set_column(col_idx, col_idx, width)
        elif col_name in ["H", "R", "ER", "BB", "K", "AB", "RBI", "HR", "2B", "3B", "SO"]:
            worksheet.set_column(col_idx, col_idx, 6)
        else:
            # Default width
            header_len = len(str(col_name)) + 2
            worksheet.set_column(col_idx, col_idx, max(header_len, 12))
    
    # Write data with proper formatting
    for row_idx in range(len(df)):
        excel_row = row_idx + 1
        is_even_row = excel_row % 2 == 1
        
        for col_idx, col_name in enumerate(df.columns):
            if col_name in exclude_cols:
                continue
                
            value = df.iloc[row_idx, col_idx]
            
            if pd.isna(value) or value == "":
                continue
            
            # Choose format based on column and row
            if col_name == "Date":
                fmt = even_date if is_even_row else odd_date
                worksheet.write_string(excel_row, col_idx, str(value), fmt)
            elif col_name in ["Team", "Opponent", "Home/Away", "Inning", "Position"]:
                fmt = even_center if is_even_row else odd_center
                worksheet.write_string(excel_row, col_idx, str(value), fmt)
            elif col_name in ["Player", "Replaced Player", "Pitcher"]:
                fmt = even_text if is_even_row else odd_text
                worksheet.write_string(excel_row, col_idx, str(value), fmt)
            elif col_name in ["H", "R", "ER", "BB", "K", "AB", "RBI", "HR", "2B", "3B", "SO", 
                "BF", "Pitches", "Swinging K", "Looking K", "Outs", "HR Count"]:
                fmt = even_number if is_even_row else odd_number
                _write_numeric_cell(worksheet, excel_row, col_idx, value, fmt)
            elif col_name == "IP":
                ip_fmt_even, ip_fmt_odd = create_format_pair(workbook, colors, num_format='0.0', align='center')
                fmt = ip_fmt_even if is_even_row else ip_fmt_odd
                _write_numeric_cell(worksheet, excel_row, col_idx, value, fmt)
            elif col_name == "WHIP":
                whip_fmt_even, whip_fmt_odd = create_format_pair(workbook, colors, num_format='0.000', align='center')
                fmt = whip_fmt_even if is_even_row else whip_fmt_odd
                _write_numeric_cell(worksheet, excel_row, col_idx, value, fmt)
            elif col_name in ["Plays", "Players", "Pitchers", "Detail", "Description"]:
                fmt = even_wrap if is_even_row else odd_wrap
                worksheet.write_string(excel_row, col_idx, str(value), fmt)
            else:
                fmt = even_text if is_even_row else odd_text
                worksheet.write_string(excel_row, col_idx, str(value), fmt)
    
    # Add hyperlinks for Player ID if present
    _add_player_id_hyperlinks(worksheet, df, workbook, colors)
    
    # Freeze header row
    worksheet.freeze_panes(1, 0)

def add_hyperlinks_to_player_ids(worksheet, df, player_id_column, workbook, colors):
    """
    Add hyperlinks to Player ID column while preserving the alternating row colors.
    This should be called AFTER the main data writing to overlay hyperlinks.
    """
    if player_id_column not in df.columns:
        return
        
    player_id_col = df.columns.get_loc(player_id_column)
    
    for row_idx in range(len(df)):
        excel_row = row_idx + 1  # Excel rows are 1-based, skip header
        player_id = df.iloc[row_idx][player_id_column]
        
        if player_id and player_id != "UNKNOWN":
            first_letter = player_id[0].lower()
            url = f"https://www.baseball-reference.com/players/{first_letter}/{player_id}.shtml"
            
            # Create hyperlink format that matches the existing row colors
            is_even_row = excel_row % 2 == 1
            bg_color = colors['white'] if is_even_row else colors['light_gray']
            
            hyperlink_format = workbook.add_format({
                'font_color': 'blue',
                'underline': True,
                'align': 'center',
                'border': 1,
                'bg_color': bg_color
            })
            
            worksheet.write_url(excel_row, player_id_col, url, hyperlink_format, string=player_id)

# Legacy helper functions for backward compatibility
def _freeze_header(ws):
    """Freeze the header row."""
    try:
        ws.freeze_panes(1, 0)
    except (AttributeError, RuntimeError):
        # Worksheet doesn't support freeze_panes or is closed
        pass

def _autofit_columns(ws, df, workbook, min_width=6, max_width=60, pad=2, wrap_cols=None, date_cols=("Date",)):
    """Best-effort autofit based on header & sample cell text length."""
    if df is None or getattr(df, "empty", False):
        return
    header_fmt = workbook.add_format({"bold": True})
    wrap_fmt = workbook.add_format({"text_wrap": True})
    date_fmt = workbook.add_format({"num_format": "mm/dd/yyyy"})
    
    for colx, colname in enumerate(df.columns):
        try:
            ws.write(0, colx, colname, header_fmt)
        except (AttributeError, RuntimeError, TypeError):
            # Worksheet write failed, skip this column header
            pass
    
    for colx, colname in enumerate(df.columns):
        width = len(str(colname)) + pad
        series = df[colname].astype(str)
        if len(series) > 0:
            sample = series.head(500)
            try:
                width = max(width, min(max(sample.str.len().max() + pad, min_width), max_width))
            except (ValueError, TypeError, AttributeError):
                width = max(width, min_width)
        
        cell_format = None
        if wrap_cols and colname in wrap_cols:
            cell_format = wrap_fmt
        elif colname in date_cols:
            cell_format = date_fmt
        
        try:
            if cell_format:
                ws.set_column(colx, colx, width, cell_format)
            else:
                ws.set_column(colx, colx, width)
        except (AttributeError, RuntimeError, TypeError):
            # Worksheet column formatting failed
            pass

def _format_common_columns(ws, df, workbook):
    """Apply common number formats to baseball stats columns if present."""
    if df is None or getattr(df, "empty", False):
        return
    
    format_mapping = {
        "AVG": "0.000", "OBP": "0.000", "SLG": "0.000", "OPS": "0.000",
        "ERA": "0.00", "Win%": "0.0%", "Game Length": "h:mm",
        "G": "0", "GS": "0", "W": "0", "L": "0", "SV": "0",
        "R": "0", "H": "0", "RBI": "0", "HR": "0", "2B": "0",
        "3B": "0", "SB": "0", "CS": "0", "BB": "0", "SO": "0",
        "TB": "0", "XBH": "0", "PA": "0", "Outs": "0", "Pitches": "0",
        "Games": "0", "Innings": "0", "Value": "0"
    }
    
    for colx, colname in enumerate(df.columns):
        num_format = format_mapping.get(str(colname))
        if num_format:
            try:
                fmt = workbook.add_format({"num_format": num_format})
                ws.set_column(colx, colx, 12, fmt)
            except (AttributeError, RuntimeError, TypeError):
                # Format creation or application failed
                pass

def _wrap_long_text(ws, df, workbook, columns=("Detail", "Description", "Plays")):
    """Wrap long text columns and give them a comfortable width."""
    if df is None or getattr(df, "empty", False):
        return
    fmt = workbook.add_format({"text_wrap": True})
    for colx, colname in enumerate(df.columns):
        if str(colname) in columns:
            try:
                ws.set_column(colx, colx, 40, fmt)
            except (AttributeError, RuntimeError, TypeError):
                # Column wrapping failed
                pass

def polish_last_sheet(writer, df, sheet_name, wrap_cols=("Detail","Description","Plays"), date_cols=("Date",)):
    """
    Call this immediately after df.to_excel(..., sheet_name=sheet_name, ...).
    It finds the worksheet and applies header freeze, autofit, numeric/date formats, and wrapping.
    """
    try:
        ws = writer.sheets.get(sheet_name)
        if ws is None:
            return
        workbook = writer.book
        _freeze_header(ws)
        _autofit_columns(ws, df, workbook, wrap_cols=wrap_cols, date_cols=date_cols)
        _format_common_columns(ws, df, workbook)
        _wrap_long_text(ws, df, workbook, columns=wrap_cols)
    except (AttributeError, KeyError, RuntimeError, TypeError) as e:
        # formatting is best-effort; never break the export
        # but log for debugging
        logging.warning(f"Sheet formatting failed for {sheet_name}: {e}")