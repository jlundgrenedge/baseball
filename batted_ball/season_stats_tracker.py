"""
Season Statistics Tracking

Provides integration between SeasonSimulator and the statistics database.
Enables tracking individual player statistics across a full season simulation.
"""

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import sqlite3

from .scorekeeper import GameLog, PlayerGameBatting, PlayerGamePitching
from .stats_database import StatsDatabase


class SeasonStatsTracker:
    """
    Tracks player statistics across a season simulation.
    
    Receives game logs from simulated games and persists them to the
    stats database, accumulating season totals for batting and pitching.
    
    Usage:
        # Start fresh
        tracker = SeasonStatsTracker.new_season(year=2025)
        
        # Or continue existing
        tracker = SeasonStatsTracker.continue_season(season_id=5)
        
        # After each game
        tracker.record_game(game_log)
        
        # Get season totals
        batting_leaders = tracker.get_batting_leaders('home_runs')
        pitching_leaders = tracker.get_pitching_leaders('strikeouts')
    """
    
    def __init__(
        self,
        year: int = 2025,
        description: str = "",
        db_path: Path = None,
        season_id: int = None,
    ):
        """
        Initialize season stats tracker.
        
        Parameters
        ----------
        year : int
            Season year
        description : str
            Description of this simulation run
        db_path : Path, optional
            Custom database path
        season_id : int, optional
            Existing season ID to continue (if provided, uses this instead of creating new)
        """
        self.year = year
        self.db = StatsDatabase(db_path)
        
        if season_id is not None:
            # Continue existing season
            self.season_id = season_id
            info = self.db.get_season_info(season_id)
            if info:
                self.year = info['year']
                self.games_recorded = info['games_played']
            else:
                raise ValueError(f"Season ID {season_id} not found")
        else:
            # Create new season
            self.season_id = self.db.start_season(year, description)
            self.games_recorded = 0
        
        self.errors: List[str] = []
    
    @classmethod
    def new_season(
        cls, 
        year: int = 2025, 
        description: str = "",
        db_path: Path = None
    ) -> 'SeasonStatsTracker':
        """
        Create a new season (always fresh, never continues existing).
        
        Parameters
        ----------
        year : int
            Season year
        description : str
            Description of this simulation run
        db_path : Path, optional
            Custom database path
        
        Returns
        -------
        SeasonStatsTracker
            New tracker with fresh season
        """
        return cls(year=year, description=description, db_path=db_path)
    
    @classmethod
    def continue_season(
        cls, 
        season_id: int,
        db_path: Path = None
    ) -> 'SeasonStatsTracker':
        """
        Continue an existing season.
        
        Parameters
        ----------
        season_id : int
            The season ID to continue
        db_path : Path, optional
            Custom database path
        
        Returns
        -------
        SeasonStatsTracker
            Tracker continuing the existing season
        """
        return cls(season_id=season_id, db_path=db_path)
    
    @classmethod
    def list_available_seasons(
        cls, 
        year: int = None,
        db_path: Path = None
    ) -> List[Dict]:
        """
        List all available seasons in the database.
        
        Parameters
        ----------
        year : int, optional
            Filter by year
        db_path : Path, optional
            Custom database path
        
        Returns
        -------
        list of dict
            Season records with id, year, games, etc.
        """
        db = StatsDatabase(db_path)
        return db.list_seasons(year)
    
    @classmethod
    def delete_season(cls, season_id: int, db_path: Path = None) -> bool:
        """
        Delete a season and all its data.
        
        Parameters
        ----------
        season_id : int
            The season to delete
        db_path : Path, optional
            Custom database path
        
        Returns
        -------
        bool
            True if deleted
        """
        db = StatsDatabase(db_path)
        return db.delete_season(season_id)
    
    @classmethod
    def prompt_season_choice(cls, year: int = 2025, db_path: Path = None) -> 'SeasonStatsTracker':
        """
        Interactive prompt to choose new or existing season.
        
        Parameters
        ----------
        year : int
            Default year for new season
        db_path : Path, optional
            Custom database path
        
        Returns
        -------
        SeasonStatsTracker
            Tracker for chosen season
        """
        db = StatsDatabase(db_path)
        seasons = db.list_seasons()
        
        print("\n" + "=" * 60)
        print("  SEASON STATS DATABASE")
        print("=" * 60)
        
        if seasons:
            print("\nExisting seasons:")
            print("-" * 60)
            for i, s in enumerate(seasons, 1):
                status = "Complete" if s['is_complete'] else "In Progress"
                desc = s['description'] or "No description"
                games = s['total_games']
                print(f"  {i}. {s['year']} Season (ID: {s['season_id']})")
                print(f"     {games} games | {status} | {desc}")
            print()
        
        print("Options:")
        print("  N - Start NEW season")
        if seasons:
            print("  C - CONTINUE an existing season")
            print("  D - DELETE a season")
        print("  Q - Quit")
        print()
        
        while True:
            choice = input("Choice: ").strip().upper()
            
            if choice == 'Q':
                return None
            
            if choice == 'N':
                desc = input(f"Description for {year} season (optional): ").strip()
                return cls.new_season(year=year, description=desc, db_path=db_path)
            
            if choice == 'C' and seasons:
                try:
                    idx = int(input("Enter season number to continue: ")) - 1
                    if 0 <= idx < len(seasons):
                        season_id = seasons[idx]['season_id']
                        print(f"Continuing season {seasons[idx]['year']} (ID: {season_id})")
                        return cls.continue_season(season_id=season_id, db_path=db_path)
                except ValueError:
                    pass
                print("Invalid selection")
                continue
            
            if choice == 'D' and seasons:
                try:
                    idx = int(input("Enter season number to DELETE: ")) - 1
                    if 0 <= idx < len(seasons):
                        season_id = seasons[idx]['season_id']
                        confirm = input(f"Delete season {seasons[idx]['year']} (ID: {season_id})? (yes/no): ")
                        if confirm.lower() == 'yes':
                            cls.delete_season(season_id, db_path)
                            print("Deleted!")
                            # Refresh and continue prompting
                            return cls.prompt_season_choice(year, db_path)
                except ValueError:
                    pass
                print("Invalid selection")
                continue
            
            print("Invalid choice")

    def record_game(self, game_log: GameLog) -> bool:
        """
        Record a game's statistics to the database.
        
        Parameters
        ----------
        game_log : GameLog
            Complete game log from Scorekeeper
        
        Returns
        -------
        bool
            True if successful
        """
        try:
            self.db.record_game(self.season_id, game_log)
            self.games_recorded += 1
            return True
        except Exception as e:
            self.errors.append(f"Game {game_log.game_id}: {e}")
            return False
    
    def get_batting_leaders(self, stat: str, limit: int = 10, min_pa: int = 0) -> List[Dict]:
        """Get batting leaderboard for a statistic."""
        return self.db.get_batting_leaders(self.season_id, stat, limit, min_pa)
    
    def get_pitching_leaders(self, stat: str, limit: int = 10, min_ip: float = 0) -> List[Dict]:
        """Get pitching leaderboard for a statistic."""
        return self.db.get_pitching_leaders(self.season_id, stat, limit, min_ip)
    
    def get_standings(self) -> List[Dict]:
        """Get team standings."""
        return self.db.get_team_standings(self.season_id)
    
    def get_season_summary(self) -> Dict:
        """Get season summary statistics."""
        return self.db.get_season_summary(self.season_id)
    
    def get_player_game_log(self, player_id: str, is_batting: bool = True) -> List[Dict]:
        """Get game-by-game log for a player."""
        return self.db.get_player_game_log(self.season_id, player_id, is_batting)
    
    def complete_season(self):
        """Mark the season as complete."""
        self.db.complete_season(self.season_id)
    
    def print_batting_leaders(self, limit: int = 10, min_pa: int = 50):
        """Print formatted batting leaders."""
        print("\n" + "=" * 70)
        print(f"  BATTING LEADERS (Season {self.year}, {self.games_recorded} games)")
        print("=" * 70)
        
        # Home Runs
        print("\nHome Runs:")
        for player in self.get_batting_leaders('home_runs', limit, min_pa):
            print(f"  {player['player_name']:<25} {player['team']} {player['home_runs']:>3} HR")
        
        # Batting Average
        print("\nBatting Average (min 50 PA):")
        for player in self.get_batting_leaders('batting_avg', limit, min_pa):
            avg = player.get('batting_avg', 0)
            if avg:
                print(f"  {player['player_name']:<25} {player['team']} .{int(avg*1000):03d}")
        
        # RBI
        print("\nRBIs:")
        for player in self.get_batting_leaders('rbi', limit, min_pa):
            print(f"  {player['player_name']:<25} {player['team']} {player['rbi']:>3} RBI")
    
    def print_pitching_leaders(self, limit: int = 10, min_ip: float = 10):
        """Print formatted pitching leaders."""
        print("\n" + "=" * 70)
        print(f"  PITCHING LEADERS (Season {self.year}, {self.games_recorded} games)")
        print("=" * 70)
        
        # Wins
        print("\nWins:")
        for player in self.get_pitching_leaders('wins', limit, min_ip):
            print(f"  {player['player_name']:<25} {player['team']} {player['wins']:>2} W")
        
        # Strikeouts
        print("\nStrikeouts:")
        for player in self.get_pitching_leaders('strikeouts', limit, min_ip):
            print(f"  {player['player_name']:<25} {player['team']} {player['strikeouts']:>3} K")
        
        # ERA (min 10 IP)
        print(f"\nERA (min {min_ip} IP):")
        for player in self.get_pitching_leaders('era', limit, min_ip):
            era = player.get('era', 0)
            if era is not None:
                print(f"  {player['player_name']:<25} {player['team']} {era:>5.2f}")
    
    def close(self):
        """Close database connection."""
        self.db.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def serialize_game_log(game_log: GameLog) -> Dict:
    """
    Serialize a GameLog to a dictionary for IPC.
    
    This is used when game logs need to be passed between
    parallel worker processes.
    """
    return {
        'game_id': game_log.game_id,
        'game_date': game_log.game_date.isoformat(),
        'away_team': game_log.away_team,
        'home_team': game_log.home_team,
        'away_score': game_log.away_score,
        'home_score': game_log.home_score,
        'away_line': game_log.away_line,
        'home_line': game_log.home_line,
        'away_hits': game_log.away_hits,
        'home_hits': game_log.home_hits,
        'away_errors': game_log.away_errors,
        'home_errors': game_log.home_errors,
        
        'away_batting': [_serialize_batting(s) for s in game_log.away_batting],
        'home_batting': [_serialize_batting(s) for s in game_log.home_batting],
        'away_pitching': [_serialize_pitching(s) for s in game_log.away_pitching],
        'home_pitching': [_serialize_pitching(s) for s in game_log.home_pitching],
    }


def deserialize_game_log(data: Dict) -> GameLog:
    """Deserialize a dictionary back to a GameLog."""
    return GameLog(
        game_id=data['game_id'],
        game_date=date.fromisoformat(data['game_date']),
        away_team=data['away_team'],
        home_team=data['home_team'],
        innings=[],  # Not needed for database
        away_score=data['away_score'],
        home_score=data['home_score'],
        away_line=data['away_line'],
        home_line=data['home_line'],
        away_batting=[_deserialize_batting(s) for s in data['away_batting']],
        home_batting=[_deserialize_batting(s) for s in data['home_batting']],
        away_pitching=[_deserialize_pitching(s) for s in data['away_pitching']],
        home_pitching=[_deserialize_pitching(s) for s in data['home_pitching']],
        away_hits=data['away_hits'],
        home_hits=data['home_hits'],
        away_errors=data['away_errors'],
        home_errors=data['home_errors'],
    )


def _serialize_batting(stats: PlayerGameBatting) -> Dict:
    """Serialize batting stats."""
    return {
        'player_id': stats.player_id,
        'player_name': stats.player_name,
        'team': stats.team,
        'position': stats.position,
        'batting_order': stats.batting_order,
        'plate_appearances': stats.plate_appearances,
        'at_bats': stats.at_bats,
        'runs': stats.runs,
        'hits': stats.hits,
        'doubles': stats.doubles,
        'triples': stats.triples,
        'home_runs': stats.home_runs,
        'rbi': stats.rbi,
        'walks': stats.walks,
        'strikeouts': stats.strikeouts,
        'hit_by_pitch': stats.hit_by_pitch,
        'sacrifice_flies': stats.sacrifice_flies,
        'sacrifice_bunts': stats.sacrifice_bunts,
        'stolen_bases': stats.stolen_bases,
        'caught_stealing': stats.caught_stealing,
        'gidp': stats.gidp,
        'exit_velocities': stats.exit_velocities,
        'launch_angles': stats.launch_angles,
    }


def _deserialize_batting(data: Dict) -> PlayerGameBatting:
    """Deserialize batting stats."""
    return PlayerGameBatting(
        player_id=data['player_id'],
        player_name=data['player_name'],
        team=data['team'],
        position=data.get('position'),
        batting_order=data.get('batting_order', 0),
        plate_appearances=data.get('plate_appearances', 0),
        at_bats=data.get('at_bats', 0),
        runs=data.get('runs', 0),
        hits=data.get('hits', 0),
        doubles=data.get('doubles', 0),
        triples=data.get('triples', 0),
        home_runs=data.get('home_runs', 0),
        rbi=data.get('rbi', 0),
        walks=data.get('walks', 0),
        strikeouts=data.get('strikeouts', 0),
        hit_by_pitch=data.get('hit_by_pitch', 0),
        sacrifice_flies=data.get('sacrifice_flies', 0),
        sacrifice_bunts=data.get('sacrifice_bunts', 0),
        stolen_bases=data.get('stolen_bases', 0),
        caught_stealing=data.get('caught_stealing', 0),
        gidp=data.get('gidp', 0),
        exit_velocities=data.get('exit_velocities', []),
        launch_angles=data.get('launch_angles', []),
    )


def _serialize_pitching(stats: PlayerGamePitching) -> Dict:
    """Serialize pitching stats."""
    return {
        'player_id': stats.player_id,
        'player_name': stats.player_name,
        'team': stats.team,
        'outs_recorded': stats.outs_recorded,
        'hits_allowed': stats.hits_allowed,
        'runs_allowed': stats.runs_allowed,
        'earned_runs': stats.earned_runs,
        'walks': stats.walks,
        'strikeouts': stats.strikeouts,
        'home_runs_allowed': stats.home_runs_allowed,
        'hit_batters': stats.hit_batters,
        'batters_faced': stats.batters_faced,
        'pitches': stats.pitches,
        'ground_balls': stats.ground_balls,
        'fly_balls': stats.fly_balls,
        'line_drives': stats.line_drives,
        'win': stats.win,
        'loss': stats.loss,
        'save': stats.save,
        'hold': stats.hold,
        'blown_save': stats.blown_save,
    }


def _deserialize_pitching(data: Dict) -> PlayerGamePitching:
    """Deserialize pitching stats."""
    return PlayerGamePitching(
        player_id=data['player_id'],
        player_name=data['player_name'],
        team=data['team'],
        outs_recorded=data.get('outs_recorded', 0),
        hits_allowed=data.get('hits_allowed', 0),
        runs_allowed=data.get('runs_allowed', 0),
        earned_runs=data.get('earned_runs', 0),
        walks=data.get('walks', 0),
        strikeouts=data.get('strikeouts', 0),
        home_runs_allowed=data.get('home_runs_allowed', 0),
        hit_batters=data.get('hit_batters', 0),
        batters_faced=data.get('batters_faced', 0),
        pitches=data.get('pitches', 0),
        ground_balls=data.get('ground_balls', 0),
        fly_balls=data.get('fly_balls', 0),
        line_drives=data.get('line_drives', 0),
        win=data.get('win', False),
        loss=data.get('loss', False),
        save=data.get('save', False),
        hold=data.get('hold', False),
        blown_save=data.get('blown_save', False),
    )
