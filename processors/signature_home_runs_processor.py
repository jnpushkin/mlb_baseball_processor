import os
import pandas as pd
from ..excel.generators import ExcelGeneratorUtils
from ..utils.helpers import standardize_team_code
from ..utils.constants import SPLASH_HITS_FILE, MCCOVEY_COVE_FILE, EUTAW_FILE, POOL_HR_FILE

class SignatureHomeRunsProcessor:
    """Handle signature home runs (splash hits, Eutaw Street, pool HRs) with improved organization."""
    
    def __init__(self, games):
        self.games = games
        
    def process_signature_home_runs(self):
        """Process splash hits, Eutaw Street HRs, and pool HRs."""
        print("🏟️ Processing signature home runs...")
        
        # Load all reference data
        reference_data = self._load_reference_data()
        
        if not reference_data:
            print("   🔍 No signature home runs found")
            return pd.DataFrame()
        
        # Process games for matches
        signature_matches = []
        matches_by_type = {"Splash Hit": 0, "McCovey Cove HR": 0, "Eutaw HR": 0, "Pool HR": 0}
        
        for game in self.games:
            matches = self._process_game_for_signature_hrs(game, reference_data)
            signature_matches.extend(matches)
            for match in matches:
                match_type = match.get("Type", "Unknown")
                if match_type in matches_by_type:
                    matches_by_type[match_type] += 1
        
        # Report breakdown by type
        print(f"   📊 Signature HR breakdown:")
        for hr_type, count in matches_by_type.items():
            if count > 0:
                print(f"      - {hr_type}: {count}")
        
        # Create final DataFrame
        df_signature = self._create_signature_dataframe(signature_matches)
        
        print(f"   ✅ Found {len(signature_matches)} signature home runs total")
        return df_signature
    
    def _load_reference_data(self):
        """Load and prepare all signature HR reference data."""
        try:
            reference_data = {}
            
            # Load splash hits data (Giants)
            if os.path.exists(SPLASH_HITS_FILE):
                splash_giants = pd.read_csv(SPLASH_HITS_FILE)
                splash_giants = splash_giants.rename(columns={"Splash Hit Number": "SplashNumber"})
                splash_giants["Type"] = "Splash Hit"
                
                # Parse dates and create Date_yyyymmdd column
                splash_giants = self._prepare_date_column(splash_giants)
                reference_data['splash_giants'] = splash_giants
                print(f"   📊 Loaded {len(splash_giants)} Giants splash hits")
            
            # Load McCovey Cove HRs (visitor splash hits) 
            if os.path.exists(MCCOVEY_COVE_FILE):
                splash_visitors = pd.read_csv(MCCOVEY_COVE_FILE)
                
                if "Splash Hit Number" in splash_visitors.columns:
                    splash_visitors = splash_visitors.rename(columns={"Splash Hit Number": "SplashNumber"})
                
                splash_visitors["Type"] = "McCovey Cove HR"
                
                # Ensure Date_yyyymmdd exists and is properly formatted
                if "Date_yyyymmdd" not in splash_visitors.columns:
                    splash_visitors = self._prepare_date_column(splash_visitors)
                else:
                    # Ensure it's a string in YYYYMMDD format
                    splash_visitors["Date_yyyymmdd"] = splash_visitors["Date_yyyymmdd"].astype(str).str.zfill(8)
                
                reference_data["splash_visitors"] = splash_visitors
                print(f"   📊 Loaded {len(splash_visitors)} visitor McCovey Cove HRs")
            
            # Load Eutaw Street HRs
            if os.path.exists(EUTAW_FILE):
                eutaw_df = pd.read_csv(EUTAW_FILE)
                eutaw_df = eutaw_df.rename(columns={"Eutaw Street HR #": "EutawNumber"})
                eutaw_df = self._prepare_date_column(eutaw_df)
                reference_data['eutaw'] = eutaw_df
                print(f"   📊 Loaded {len(eutaw_df)} Eutaw Street HRs")
            
            # Load pool HRs (now with PlayerID column)
            if os.path.exists(POOL_HR_FILE):
                pool_df = pd.read_csv(POOL_HR_FILE)
                pool_df = self._prepare_date_column(pool_df)
                
                # Verify PlayerID column exists
                if "PlayerID" not in pool_df.columns:
                    print(f"   ⚠️ WARNING: Chase Field CSV missing PlayerID column - pool HRs will not be matched")
                
                reference_data['pool'] = pool_df
                print(f"   📊 Loaded {len(pool_df)} Chase Field pool HRs")
            
            total_records = sum(len(df) for df in reference_data.values() if isinstance(df, pd.DataFrame))
            print(f"   📊 Total signature HR records loaded: {total_records}")
            
            return reference_data
            
        except Exception as e:
            print(f"   ⚠️ Error loading reference data: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _prepare_date_column(self, df):
        """Prepare consistent Date_yyyymmdd column from various date formats with smart 2-digit year handling."""
        try:
            if "Date" not in df.columns:
                print(f"   ⚠️ No Date column found in dataframe")
                return df
            
            # Create a copy of the date series for processing
            date_series = df["Date"].copy()
            parsed_dates = pd.Series([pd.NaT] * len(date_series), index=date_series.index)
            
            # Process each date individually
            for i, raw_date in enumerate(date_series):
                if pd.isna(raw_date) or raw_date == "":
                    continue
                    
                date_str = str(raw_date).strip()
                parsed_date = None
                
                # Step 1: Handle ambiguous 2-digit years first (smart recent date assumption)
                if self._is_ambiguous_2digit_year(date_str):
                    corrected_date = self._fix_2digit_year(date_str)
                    try:
                        parsed_date = pd.to_datetime(corrected_date, format="%m/%d/%Y")
                    except:
                        pass
                
                # Step 2: Try standard date formats
                if parsed_date is None or pd.isna(parsed_date):
                    date_formats = [
                        "%m/%d/%Y",  # 04/15/2023, 8/29/2025
                        "%m/%d/%y",  # 04/15/23 (will use Python's default pivot)
                        "%Y-%m-%d",  # 2023-04-15
                        "%B %d, %Y", # April 15, 2023
                        "%b %d, %Y", # Apr 15, 2023
                    ]
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = pd.to_datetime(date_str, format=fmt)
                            if pd.notna(parsed_date):
                                break
                        except:
                            continue
                
                # Step 3: Fallback to pandas general parser
                if parsed_date is None or pd.isna(parsed_date):
                    try:
                        parsed_date = pd.to_datetime(date_str, errors='coerce')
                    except:
                        parsed_date = pd.NaT
                
                # Store the result
                parsed_dates[i] = parsed_date
            
            # Add parsed dates to dataframe
            df["Date_parsed"] = parsed_dates
            df["Date_yyyymmdd"] = df["Date_parsed"].dt.strftime("%Y%m%d")
            
            # Report any dates that couldn't be parsed
            failed_dates = df[df["Date_parsed"].isna()]
            if len(failed_dates) > 0:
                print(f"   ⚠️ Failed to parse {len(failed_dates)} dates")
                if len(failed_dates) <= 5:
                    for _, row in failed_dates.iterrows():
                        print(f"      - '{row.get('Date', 'N/A')}' for {row.get('Player', 'Unknown')}")
            
            # Drop rows with unparseable dates
            initial_count = len(df)
            df = df.dropna(subset=["Date_parsed"])
            if len(df) < initial_count:
                print(f"   📝 Removed {initial_count - len(df)} rows with invalid dates")
            
            return df
            
        except Exception as e:
            print(f"   ⚠️ Error preparing date column: {e}")
            return df

    def _is_ambiguous_2digit_year(self, date_str):
        """Check if date string has ambiguous 2-digit year format."""
        import re
        # Match formats like "8/29/25", "12/15/23", etc.
        return bool(re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_str))

    def _fix_2digit_year(self, date_str):
        """Convert 2-digit year to 4-digit assuming recent dates for baseball context."""
        import re
        
        # Extract month, day, year
        match = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{2})$', date_str)
        if not match:
            return date_str
        
        month, day, year_2digit = match.groups()
        year_int = int(year_2digit)
        
        # Baseball context: assume recent dates
        # Years 00-40 = 2000-2040 (covers current era + future)
        # Years 41-99 = 1941-1999 (covers historical baseball)
        # This cutoff assumes no baseball records from 1900-1940 in your dataset
        if year_int <= 40:
            full_year = 2000 + year_int
        else:
            full_year = 1900 + year_int
        
        corrected = f"{month}/{day}/{full_year}"
        return corrected

    def _validate_parsed_date(self, parsed_date, original_str, player_name="Unknown"):
        """Validate that parsed date makes sense for baseball context."""
        if pd.isna(parsed_date):
            return False
        
        # Baseball context validation
        year = parsed_date.year
        
        # Reasonable range for baseball records (1900-2030)
        if year < 1900 or year > 2030:
            print(f"   ⚠️ Suspicious year {year} for {player_name} from '{original_str}' - may need manual review")
            return False
        
        # Warn about very old dates that might be parsing errors
        if year < 1950:
            print(f"   📅 Very old date {year} for {player_name} - please verify '{original_str}' is correct")
        
        return True

    def _process_game_for_signature_hrs(self, game, reference_data):
        """Process a single game for signature home run matches."""
        basic_info = game.get("basic_info", {})
        game_id = ExcelGeneratorUtils.safe_get_str(game, "game_id", "UNKNOWN")
        date_str = ExcelGeneratorUtils.safe_get_str(basic_info, "date_yyyymmdd", "").strip()
        venue = ExcelGeneratorUtils.safe_get_str(basic_info, "venue", "").lower()
        
        matches = []
        
        # Check for splash hits at Oracle/AT&T Park
        if "oracle park" in venue or "at&t park" in venue:
            matches.extend(self._check_splash_hits(game, date_str, game_id, reference_data))
        
        # Check for Eutaw Street HRs at Oriole Park
        elif "oriole park" in venue or "camden yards" in venue:
            matches.extend(self._check_eutaw_hits(game, date_str, game_id, reference_data))
        
        # Check for pool HRs at Chase Field
        elif "chase field" in venue:
            matches.extend(self._check_pool_hits(game, date_str, game_id, reference_data))
        
        return matches
    
    def _check_splash_hits(self, game, date_str, game_id, reference_data):
        """Check for splash hits and McCovey Cove HRs - matching by PlayerID only."""
        matches = []
        
        # Get player IDs from the game
        batter_ids = self._get_batter_ids(game)
        
        # Check Giants splash hits
        if 'splash_giants' in reference_data:
            giants_hits = reference_data['splash_giants'].copy()
            giants_hits["Date_yyyymmdd"] = giants_hits["Date_yyyymmdd"].astype(str).str.strip()
            date_matches = giants_hits[giants_hits["Date_yyyymmdd"] == date_str]
            
            for _, row in date_matches.iterrows():
                player_id = ExcelGeneratorUtils.safe_get_str(row, "PlayerID", "").strip()
                
                # Only match by PlayerID
                if player_id and player_id in batter_ids:
                    match = self._create_signature_match(row, game_id, "Splash Hit", is_visitor=False)
                    if match:
                        matches.append(match)
        
        # Check visitor McCovey Cove HRs
        if 'splash_visitors' in reference_data:
            visitor_hits = reference_data['splash_visitors'].copy()
            visitor_hits["Date_yyyymmdd"] = visitor_hits["Date_yyyymmdd"].astype(str).str.strip()
            date_matches = visitor_hits[visitor_hits["Date_yyyymmdd"] == date_str]
            
            for _, row in date_matches.iterrows():
                player_id = ExcelGeneratorUtils.safe_get_str(row, "PlayerID", "").strip()
                
                # Only match by PlayerID
                if player_id and player_id in batter_ids:
                    match = self._create_signature_match(row, game_id, "McCovey Cove HR", is_visitor=True)
                    if match:
                        matches.append(match)
        
        return matches
    
    def _check_eutaw_hits(self, game, date_str, game_id, reference_data):
        """Check for Eutaw Street home runs - matching by PlayerID only."""
        matches = []
        
        if 'eutaw' not in reference_data:
            return matches
        
        batter_ids = self._get_batter_ids(game)
        
        eutaw_hits = reference_data['eutaw'][
            reference_data['eutaw']["Date_yyyymmdd"] == date_str
        ]
        
        for _, row in eutaw_hits.iterrows():
            player_id = ExcelGeneratorUtils.safe_get_str(row, "PlayerID", "").strip()
            
            # Only match by PlayerID
            if player_id and player_id in batter_ids:
                # Get the date - prefer Date_parsed if available
                date_value = row.get("Date_parsed", row.get("Date"))
                
                match = {
                    "Date": date_value,
                    "Player": ExcelGeneratorUtils.safe_get_str(row, "Player", ""),
                    "Team": standardize_team_code(ExcelGeneratorUtils.safe_get_str(row, "Team", "")),
                    "Opponent": standardize_team_code(ExcelGeneratorUtils.safe_get_str(row, "Pitcher Team", "")),
                    "Pitcher": ExcelGeneratorUtils.safe_get_str(row, "Pitcher", ""),
                    "GameID": game_id,
                    "Type": "Eutaw HR",
                    "HitNumber": ExcelGeneratorUtils.safe_get_int(row, "EutawNumber", None)
                }
                matches.append(match)
        
        return matches
    
    def _check_pool_hits(self, game, date_str, game_id, reference_data):
        """Check for Chase Field pool home runs - matching by PlayerID only."""
        matches = []
        
        if 'pool' not in reference_data:
            return matches
        
        # Get player IDs from game
        batter_ids = self._get_batter_ids(game)
        
        pool_hits = reference_data['pool'][
            reference_data['pool']["Date_yyyymmdd"] == date_str
        ]
        
        for _, row in pool_hits.iterrows():
            player_id = ExcelGeneratorUtils.safe_get_str(row, "PlayerID", "").strip()
            
            # Only match by PlayerID (since you're adding this column)
            if player_id and player_id in batter_ids:
                # Get the date - prefer Date_parsed if available
                date_value = row.get("Date_parsed", row.get("Date"))
                
                match = {
                    "Date": date_value,
                    "Player": ExcelGeneratorUtils.safe_get_str(row, "Player", ""),
                    "Team": standardize_team_code(ExcelGeneratorUtils.safe_get_str(row, "Team", "")),
                    "Opponent": standardize_team_code(ExcelGeneratorUtils.safe_get_str(row, "Opponent", "")),
                    "Pitcher": ExcelGeneratorUtils.safe_get_str(row, "Pitcher", ""),
                    "GameID": game_id,
                    "Type": "Pool HR",
                    "HitNumber": ExcelGeneratorUtils.safe_get_int(row, "No", None)
                }
                matches.append(match)
        
        return matches
    
    def _get_batter_ids(self, game):
        """Get set of all batter IDs from the game."""
        batter_ids = set()
        for side in ["home", "away"]:
            for player in game.get("batting", {}).get(side, []):
                player_id = player.get("player_id")
                if player_id:
                    batter_ids.add(player_id)
        return batter_ids
    
    def _get_player_names(self, game):
        """Get set of all player names from the game."""
        player_names = set()
        for side in ["home", "away"]:
            for player in game.get("batting", {}).get(side, []):
                name = player.get("name")
                if name:
                    player_names.add(name)
        return player_names
    
    def _create_signature_match(self, row, game_id, hr_type, is_visitor=False):
        """Create a signature HR match record."""
        try:
            player = ExcelGeneratorUtils.safe_get_str(row, "Player", "")
            if not player:
                return None
            
            # Determine team codes based on whether this is a visitor HR
            if is_visitor:
                team = ExcelGeneratorUtils.safe_get_str(row, "Team", "SF")
                opponent = "SF"
            else:
                team = "SF"  # Giants splash hits
                opponent = ExcelGeneratorUtils.safe_get_str(row, "Opponent", "")
            
            hit_number = None
            if "SplashNumber" in row and pd.notnull(row["SplashNumber"]):
                hit_number = int(row["SplashNumber"])
            elif "EutawNumber" in row and pd.notnull(row["EutawNumber"]):
                hit_number = int(row["EutawNumber"])
            
            # Get the date - prefer Date_parsed if available
            date_value = row.get("Date_parsed", row.get("Date"))
            
            match = {
                "Date": date_value,
                "Player": player,
                "Team": standardize_team_code(team),
                "Opponent": standardize_team_code(opponent),
                "Pitcher": ExcelGeneratorUtils.safe_get_str(row, "Pitcher", ""),
                "GameID": game_id,
                "Type": hr_type,
                "HitNumber": hit_number
            }
            
            return match
            
        except Exception as e:
            print(f"   ⚠️ Error creating signature match for {row.get('Player', 'Unknown')}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _create_signature_dataframe(self, matches):
        """Create the final signature home runs DataFrame."""
        if not matches:
            return pd.DataFrame()

        try:
            df = pd.DataFrame(matches)
            
            print(f"   📝 Creating signature DataFrame with {len(df)} matches")

            # Create signature HR number column FIRST (before any date manipulation)
            if "Type" in df.columns and "HitNumber" in df.columns:
                df["Signature HR Number"] = df.apply(
                    lambda row: f"{row['Type']} #{int(row['HitNumber'])}"
                    if pd.notnull(row.get("HitNumber")) else row.get("Type", "Signature HR"),
                    axis=1
                )
            else:
                df["Signature HR Number"] = "Signature HR"

            # Handle Date column - convert everything to consistent format
            if "Date" in df.columns:
                # Convert all dates to datetime objects first
                date_series = pd.Series(df["Date"])
                
                # Handle both datetime objects and strings
                for i, val in enumerate(date_series):
                    if pd.api.types.is_datetime64_any_dtype(type(val)):
                        # Already a datetime
                        continue
                    elif isinstance(val, pd.Timestamp):
                        # Already a pandas Timestamp
                        continue
                    elif isinstance(val, str):
                        # Try to parse string
                        try:
                            date_series[i] = pd.to_datetime(val)
                        except:
                            print(f"   ⚠️ Could not parse date: {val}")
                            date_series[i] = pd.NaT
                
                # Convert to datetime type
                df["Date"] = pd.to_datetime(date_series, errors='coerce')
                
                # Drop rows with invalid dates
                initial_count = len(df)
                df = df.dropna(subset=["Date"])
                if len(df) < initial_count:
                    print(f"   ⚠️ Dropped {initial_count - len(df)} rows with invalid dates")
                
                # Sort by date
                df = df.sort_values("Date").reset_index(drop=True)
                
                # Format dates as MM/DD/YYYY strings for Excel
                df["Date"] = df["Date"].dt.strftime("%m/%d/%Y")

            # Clean up and reorder columns
            df = df.drop(columns=["HitNumber", "Type"], errors="ignore")

            # Keep only the expected columns that exist
            desired = ["Date", "Player", "Team", "Opponent", "Pitcher", "Signature HR Number", "GameID"]
            df = df[[c for c in desired if c in df.columns]]
            
            print(f"   ✅ Final signature DataFrame has {len(df)} rows")

            return df

        except Exception as e:
            print(f"   ⚠️ Error creating signature DataFrame: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
 