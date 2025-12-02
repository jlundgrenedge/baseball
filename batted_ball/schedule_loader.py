"""
MLB Schedule Loader for 2025 Season Simulation.

Parses the 2025 MLB schedule CSV and provides access to games by date,
supporting day-by-day simulation of the full season.
"""

import csv
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Use centralized team mappings
from batted_ball.database.team_mappings import (
    TEAM_ABBR_MAP,
    DB_TO_CSV_MAP as DB_ABBR_TO_CSV,
    get_db_abbr,
    get_team_name,
    get_all_team_abbrs,
)


@dataclass
class ScheduledGame:
    """Represents a single scheduled game."""
    date: date
    day_of_week: str
    away_team: str       # Database abbreviation (e.g., 'NYY')
    away_league: str     # 'AL' or 'NL'
    away_game_num: int   # Game number in season for away team
    home_team: str       # Database abbreviation (e.g., 'LAD')
    home_league: str     # 'AL' or 'NL'
    home_game_num: int   # Game number in season for home team
    day_night: str       # 'd' for day, 'n' for night
    location: str        # Venue code
    is_postponed: bool   # True if game was postponed
    makeup_date: Optional[str]  # Date of makeup game if postponed
    
    @property
    def is_interleague(self) -> bool:
        """Check if this is an interleague game."""
        return self.away_league != self.home_league
    
    @property
    def is_playable(self) -> bool:
        """Check if this game should be simulated.
        
        Note: We simulate ALL games on their originally scheduled date,
        regardless of real-world postponements. This ensures each team
        plays exactly 162 games.
        """
        return True  # Simulate all games on original date
    
    def __str__(self) -> str:
        day_night_str = "Day" if self.day_night == 'd' else "Night"
        status = " [POSTPONED]" if self.is_postponed else ""
        return f"{self.date}: {self.away_team} @ {self.home_team} ({day_night_str}){status}"


class ScheduleLoader:
    """
    Loads and provides access to the 2025 MLB schedule.
    
    Usage:
        loader = ScheduleLoader()
        games = loader.get_games_for_date(date(2025, 3, 27))
        all_dates = loader.get_all_game_dates()
    """
    
    def __init__(self, schedule_path: Optional[str] = None):
        """
        Initialize the schedule loader.
        
        Parameters
        ----------
        schedule_path : str, optional
            Path to the schedule CSV. If None, uses default location.
        """
        if schedule_path is None:
            # Default to data/bballsavant/2025/2025schedule.csv
            base_path = Path(__file__).parent.parent
            schedule_path = base_path / "data" / "bballsavant" / "2025" / "2025schedule.csv"
        
        self.schedule_path = Path(schedule_path)
        self.games: List[ScheduledGame] = []
        self.games_by_date: Dict[date, List[ScheduledGame]] = {}
        self._team_names: Dict[str, str] = {}  # Maps abbr to full name
        
        self._load_schedule()
    
    def _load_schedule(self):
        """Load and parse the schedule CSV."""
        if not self.schedule_path.exists():
            raise FileNotFoundError(f"Schedule file not found: {self.schedule_path}")
        
        # Use pandas to handle duplicate column names properly
        import pandas as pd
        df = pd.read_csv(self.schedule_path)
        
        for _, row in df.iterrows():
            # Parse date from YYYYMMDD format
            date_str = str(int(row['Date']))  # Handle potential float
            game_date = datetime.strptime(date_str, '%Y%m%d').date()
            
            # Map team abbreviations using centralized mapping
            away_csv = row['Visitor']
            home_csv = row['Home']
            away_abbr = get_db_abbr(away_csv)
            home_abbr = get_db_abbr(home_csv)
            
            # Get league info - pandas renames duplicates to League, League.1
            away_league = 'AL' if row['League'] == 'AL' else 'NL'
            home_league = 'AL' if row.get('League.1', row['League']) == 'AL' else 'NL'
            
            # Get game numbers
            away_game_num = int(row['Game']) if pd.notna(row['Game']) else 1
            home_game_num = int(row.get('Game.1', row['Game'])) if pd.notna(row.get('Game.1', row['Game'])) else 1
            
            # Check if postponed
            postponed = str(row.get('Postponed', '')).strip()
            is_postponed = postponed and postponed.lower() != 'nan'
            makeup_date = str(row.get('Makeup', '')).strip()
            if makeup_date.lower() == 'nan':
                makeup_date = None
            
            game = ScheduledGame(
                date=game_date,
                day_of_week=row['Day'],
                away_team=away_abbr,
                away_league=away_league,
                away_game_num=away_game_num,
                home_team=home_abbr,
                home_league=home_league,
                home_game_num=home_game_num,
                day_night=str(row.get('Day/Night', 'n')).lower(),
                location=str(row.get('Location', '')),
                is_postponed=is_postponed,
                makeup_date=makeup_date
            )
            
            self.games.append(game)
            
            # Index by date
            if game_date not in self.games_by_date:
                self.games_by_date[game_date] = []
            self.games_by_date[game_date].append(game)
    
    def get_games_for_date(self, game_date: date, include_postponed: bool = False) -> List[ScheduledGame]:
        """
        Get all games scheduled for a specific date.
        
        Parameters
        ----------
        game_date : date
            The date to get games for
        include_postponed : bool
            If True, include postponed games. Default False.
        
        Returns
        -------
        List[ScheduledGame]
            List of games for that date
        """
        games = self.games_by_date.get(game_date, [])
        if include_postponed:
            return games
        return [g for g in games if g.is_playable]
    
    def get_all_game_dates(self) -> List[date]:
        """
        Get all dates that have scheduled games.
        
        Returns
        -------
        List[date]
            Sorted list of all game dates
        """
        return sorted(self.games_by_date.keys())
    
    def get_date_range(self) -> Tuple[date, date]:
        """
        Get the first and last game dates.
        
        Returns
        -------
        Tuple[date, date]
            (first_date, last_date)
        """
        dates = self.get_all_game_dates()
        return (dates[0], dates[-1]) if dates else (None, None)
    
    def get_games_in_range(
        self, 
        start_date: date, 
        end_date: date,
        include_postponed: bool = False
    ) -> Dict[date, List[ScheduledGame]]:
        """
        Get all games within a date range.
        
        Parameters
        ----------
        start_date : date
            Start date (inclusive)
        end_date : date
            End date (inclusive)
        include_postponed : bool
            If True, include postponed games
        
        Returns
        -------
        Dict[date, List[ScheduledGame]]
            Games grouped by date
        """
        result = {}
        for game_date, games in self.games_by_date.items():
            if start_date <= game_date <= end_date:
                if include_postponed:
                    result[game_date] = games
                else:
                    playable = [g for g in games if g.is_playable]
                    if playable:
                        result[game_date] = playable
        return dict(sorted(result.items()))
    
    def get_team_schedule(self, team_abbr: str) -> List[ScheduledGame]:
        """
        Get all games for a specific team.
        
        Parameters
        ----------
        team_abbr : str
            Team abbreviation (database format, e.g., 'NYY')
        
        Returns
        -------
        List[ScheduledGame]
            All games for that team, sorted by date
        """
        team_games = [
            g for g in self.games 
            if g.away_team == team_abbr or g.home_team == team_abbr
        ]
        return sorted(team_games, key=lambda g: g.date)
    
    def get_all_teams(self) -> List[str]:
        """
        Get list of all teams in the schedule.
        
        Returns
        -------
        List[str]
            Unique team abbreviations (database format)
        """
        teams = set()
        for game in self.games:
            teams.add(game.away_team)
            teams.add(game.home_team)
        return sorted(teams)
    
    def get_season_summary(self) -> Dict:
        """
        Get summary statistics for the season schedule.
        
        Returns
        -------
        Dict
            Summary including total games, date range, etc.
        """
        total_games = len([g for g in self.games if g.is_playable])
        postponed_games = len([g for g in self.games if g.is_postponed])
        interleague_games = len([g for g in self.games if g.is_interleague and g.is_playable])
        
        first_date, last_date = self.get_date_range()
        
        return {
            'total_scheduled_games': len(self.games),
            'playable_games': total_games,
            'postponed_games': postponed_games,
            'interleague_games': interleague_games,
            'first_game_date': first_date,
            'last_game_date': last_date,
            'total_game_days': len(self.get_all_game_dates()),
            'teams': self.get_all_teams(),
            'team_count': len(self.get_all_teams()),
        }


def convert_db_abbr_to_csv(db_abbr: str) -> str:
    """Convert database abbreviation to CSV format."""
    return DB_ABBR_TO_CSV.get(db_abbr, db_abbr)


def convert_csv_abbr_to_db(csv_abbr: str) -> str:
    """Convert CSV abbreviation to database format."""
    return TEAM_ABBR_MAP.get(csv_abbr, csv_abbr)


if __name__ == "__main__":
    # Test the schedule loader
    print("=== Schedule Loader Test ===\n")
    
    try:
        loader = ScheduleLoader()
        
        summary = loader.get_season_summary()
        print(f"Season Summary:")
        print(f"  Total games: {summary['total_scheduled_games']}")
        print(f"  Playable: {summary['playable_games']}")
        print(f"  Postponed: {summary['postponed_games']}")
        print(f"  Interleague: {summary['interleague_games']}")
        print(f"  Date range: {summary['first_game_date']} to {summary['last_game_date']}")
        print(f"  Game days: {summary['total_game_days']}")
        print(f"  Teams: {summary['team_count']}")
        print()
        
        # Show first week of games
        print("First week of regular season:")
        first_date, _ = loader.get_date_range()
        
        # Find Opening Day (first day with many games, not Tokyo)
        for game_date in loader.get_all_game_dates():
            games = loader.get_games_for_date(game_date)
            if len(games) >= 10:  # Opening Day has many games
                print(f"\nOpening Day: {game_date} ({len(games)} games)")
                for game in games[:5]:  # Show first 5
                    print(f"  {game}")
                if len(games) > 5:
                    print(f"  ... and {len(games) - 5} more")
                break
        
        # Show Yankees schedule sample
        print("\n\nYankees first 5 games:")
        yankees_games = loader.get_team_schedule('NYY')[:5]
        for game in yankees_games:
            location = "home" if game.home_team == 'NYY' else "away"
            opponent = game.away_team if location == "home" else game.home_team
            print(f"  {game.date}: vs {opponent} ({location})")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure the schedule file exists at:")
        print("  data/bballsavant/2025/2025schedule.csv")
