import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os
import sys
import multiprocessing
from multiprocessing import cpu_count
from typing import Tuple
from pathlib import Path

# Add current directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from batted_ball.game_simulation import GameSimulator, create_test_team, Team
from batted_ball.database.team_loader import TeamLoader
from batted_ball.sim_metrics import DebugLevel
from batted_ball.series_metrics import SeriesMetrics
from batted_ball.constants import SimulationMode
from batted_ball.parallel_worker import (
    ParallelGameResult, 
    MockGameState, 
    simulate_game_worker
)


def parse_team_string(team_str: str) -> Tuple[str, int]:
    """Parse 'Team Name (Year)' format into (name, season)."""
    name_part = team_str.rsplit(" (", 1)[0]
    year_part = team_str.rsplit(" (", 1)[1].rstrip(")")
    return name_part, int(year_part)

# --- Helper Functions ---

@st.cache_data
def get_available_teams():
    """Load list of available teams from database."""
    db_path = "baseball_teams.db"
    if not os.path.exists(db_path):
        return []
    
    loader = TeamLoader(db_path)
    teams = loader.list_available_teams()
    loader.close()
    return teams

@st.cache_data
def load_team_cached(team_str):
    """Load a specific team object."""
    if not team_str:
        return None
        
    # Parse "Name (Year)" format
    try:
        name_part = team_str.rsplit(" (", 1)[0]
        year_part = team_str.rsplit(" (", 1)[1].rstrip(")")
        season = int(year_part)
        
        loader = TeamLoader("baseball_teams.db")
        team = loader.load_team(name_part, season=season)
        loader.close()
        return team
    except Exception as e:
        st.error(f"Error loading team {team_str}: {e}")
        return None

def draw_baseball_field(ax):
    """Draw a simple baseball field on a matplotlib axis."""
    # Field dimensions (approximate)
    # Home plate at (0,0)
    # Bases at 90ft intervals (diamond)
    # Outfield fence distance (generic)
    
    # Grass color
    ax.set_facecolor('#3b7a3b')
    
    # Infield dirt (brown)
    infield = patches.Wedge((0, 0), 95, 45, 135, color='#8b4513', alpha=0.7)
    ax.add_patch(infield)
    
    # Foul lines
    plt.plot([0, 226], [0, 226], color='white', linewidth=2) # Right field line
    plt.plot([0, -226], [0, 226], color='white', linewidth=2) # Left field line
    
    # Outfield fence (arc)
    # Simple arc from -226,226 to 226,226? No, that's a straight line.
    # Arc for fence: 325-400ft. Let's use a simple arc.
    theta = np.linspace(np.radians(45), np.radians(135), 100)
    r = 350 # Generic distance
    x_fence = r * np.cos(theta)
    y_fence = r * np.sin(theta)
    plt.plot(x_fence, y_fence, color='white', linewidth=3)
    
    # Bases
    bases_x = [0, 63.64, 0, -63.64]
    bases_y = [0, 63.64, 127.28, 63.64]
    plt.scatter(bases_x, bases_y, color='white', s=50, marker='D', zorder=5)
    
    # Pitcher's mound
    plt.scatter([0], [60.5], color='white', s=30, zorder=5)
    
    # Set limits
    ax.set_xlim(-250, 250)
    ax.set_ylim(-20, 400)
    ax.set_aspect('equal')
    ax.axis('off')

# --- Main App ---

def main():
    st.set_page_config(page_title="Baseball GM Dashboard", layout="wide")
    st.title("⚾ Baseball Simulation GM Dashboard")

    # Sidebar for Mode Selection
    mode = st.sidebar.radio("Select Mode", [
        "Single Game Deep Dive", 
        "Season Simulation (Parallel)",
        "Database Viewer"
    ])

    # Check for DB
    available_teams = get_available_teams()
    use_test_teams = False
    if not available_teams:
        st.sidebar.warning("No teams found in `baseball_teams.db`. Using synthetic test teams.")
        use_test_teams = True
        available_teams = ["Test Team A (2024)", "Test Team B (2024)"]

    # --- Mode 1: Single Game Deep Dive ---
    if mode == "Single Game Deep Dive":
        st.header("Single Game Simulation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            away_team_name = st.selectbox("Away Team", available_teams, index=0)
        with col2:
            home_team_name = st.selectbox("Home Team", available_teams, index=1 if len(available_teams) > 1 else 0)
        with col3:
            stadium = st.selectbox("Stadium", ["Generic", "Yankee Stadium", "Fenway Park", "Coors Field"])
            
        with st.expander("Weather Conditions"):
            wind_enabled = st.checkbox("Enable Wind", value=True)
        
        # Initialize session state for game results if not present
        if 'single_game_data' not in st.session_state:
            st.session_state.single_game_data = None

        if st.button("Play Ball! ⚾"):
            with st.spinner("Simulating game..."):
                # Load teams
                if use_test_teams:
                    away_team = create_test_team("Test Team A", "average")
                    home_team = create_test_team("Test Team B", "average")
                else:
                    away_team = load_team_cached(away_team_name)
                    home_team = load_team_cached(home_team_name)
                
                if away_team and home_team:
                    # Initialize Simulator
                    sim = GameSimulator(
                        away_team, 
                        home_team, 
                        ballpark=stadium, 
                        verbose=False, 
                        debug_metrics=2, 
                        wind_enabled=wind_enabled
                    )
                    
                    # Run Simulation
                    game_state = sim.simulate_game()
                    
                    # Store results in session state
                    st.session_state.single_game_data = {
                        'away_team': away_team,
                        'home_team': home_team,
                        'game_state': game_state,
                        'metrics': sim.metrics_collector.batted_ball_metrics,
                        'pbp': sim.play_by_play
                    }
                else:
                    st.error("Failed to load teams.")

        # Display Results (from Session State)
        if st.session_state.single_game_data:
            data = st.session_state.single_game_data
            away_team = data['away_team']
            home_team = data['home_team']
            game_state = data['game_state']
            bb_metrics = data['metrics']
            pbp = data['pbp']
            
            # 1. Scoreboard
            st.subheader(f"Final Score: {away_team.name} {game_state.away_score} - {home_team.name} {game_state.home_score}")
            
            # Box Score Data
            box_data = {
                "Team": [away_team.name, home_team.name],
                "Runs": [game_state.away_score, game_state.home_score],
                "Hits": [game_state.away_hits, game_state.home_hits],
                "Errors": [game_state.away_errors, game_state.home_errors],
                "HR": [game_state.away_home_runs, game_state.home_home_runs]
            }
            st.table(pd.DataFrame(box_data))
            
            # 2. Spray Chart
            st.subheader("Batted Ball Spray Chart")
            
            if bb_metrics:
                # Create figure
                fig, ax = plt.subplots(figsize=(10, 10))
                draw_baseball_field(ax)
                
                # Extract data
                x_coords = []
                y_coords = []
                colors = []
                labels = []
                
                for bb in bb_metrics:
                    # Coordinate Check:
                    # Field Layout: +X is Right Field, +Y is Center Field
                    # Matplotlib: +X is Right, +Y is Up
                    # This matches perfectly. No inversion needed.
                    
                    x_coords.append(bb.landing_x_ft)
                    y_coords.append(bb.landing_y_ft)
                    
                    if bb.actual_outcome in ['single', 'double', 'triple', 'home_run']:
                        colors.append('blue') # Hit
                        labels.append('Hit')
                    else:
                        colors.append('red') # Out
                        labels.append('Out')
                        
                df_spray = pd.DataFrame({
                    'x': x_coords,
                    'y': y_coords,
                    'outcome': labels,
                    'color': colors
                })
                
                # Plot Hits
                hits = df_spray[df_spray['outcome'] == 'Hit']
                ax.scatter(hits['x'], hits['y'], c='blue', label='Hit', alpha=0.7, edgecolors='white', s=60)
                
                # Plot Outs
                outs = df_spray[df_spray['outcome'] == 'Out']
                ax.scatter(outs['x'], outs['y'], c='red', label='Out', alpha=0.5, marker='x', s=40)
                
                ax.legend(loc='upper right')
                ax.set_title(f"Spray Chart - {len(bb_metrics)} Batted Balls")
                
                st.pyplot(fig, use_container_width=True)
            else:
                st.info("No batted ball data available.")

            # 3. Play-by-Play Log
            st.subheader("Play-by-Play Log")
            
            pbp_text = []
            for event in pbp:
                inning_str = f"{'Top' if event.is_top else 'Bot'} {event.inning}"
                pbp_text.append(f"[{inning_str}] {event.description}")
            
            st.text_area("Game Log", value="\n".join(pbp_text), height=300)

    # --- Mode 2: Season Simulation (Parallel) ---
    elif mode == "Season Simulation (Parallel)":
        st.header("Season Simulation")
        
        # Inputs
        # "Select All" functionality
        col_sel1, col_sel2 = st.columns([3, 1])
        with col_sel2:
            select_all = st.checkbox("Select All Teams")
        
        with col_sel1:
            if select_all:
                selected_teams = available_teams
                st.info(f"Selected all {len(selected_teams)} teams.")
            else:
                selected_teams = st.multiselect("Select Teams (Select at least 2)", available_teams, default=available_teams[:4] if len(available_teams) >= 4 else available_teams)
        
        col1, col2 = st.columns(2)
        with col1:
            num_games = st.number_input("Games per Matchup", min_value=1, value=10, help="Total games = (N * (N-1) / 2) * Games per Matchup")
        with col2:
            num_workers = st.number_input("Workers", min_value=1, max_value=cpu_count(), value=max(1, cpu_count() - 1), help="Number of parallel processes")
        
        # Initialize session state for season results
        if 'season_results' not in st.session_state:
            st.session_state.season_results = None
            
        if st.button("Simulate Season"):
            if len(selected_teams) < 2:
                st.error("Please select at least 2 teams.")
            else:
                # Parse team info (name, season) - we'll pass this to workers
                team_info = []  # List of (name, season)
                for t_str in selected_teams:
                    name, season = parse_team_string(t_str)
                    team_info.append((name, season))
                
                # Calculate totals
                num_teams = len(team_info)
                total_matchups = num_teams * (num_teams - 1) // 2
                total_games = total_matchups * num_games
                
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                # Build list of all games to simulate
                # Each game is (game_number, away_name, away_season, home_name, home_season)
                game_args = []
                game_num = 0
                for i, (away_name, away_season) in enumerate(team_info):
                    for j, (home_name, home_season) in enumerate(team_info):
                        if i >= j:
                            continue
                        for _ in range(num_games):
                            game_args.append((game_num, away_name, away_season, home_name, home_season))
                            game_num += 1
                
                # Initialize records
                team_records = {name: {'wins': 0, 'losses': 0, 'runs_for': 0, 'runs_against': 0}
                                for name, _ in team_info}
                all_game_results = []
                
                # Create SeriesMetrics for aggregate stats
                series_metrics = SeriesMetrics(
                    away_team_name="Various (Away)",
                    home_team_name="Various (Home)"
                )
                
                start_time = pd.Timestamp.now()
                progress_text.text(f"Starting parallel simulation with {num_workers} workers...")
                
                # Run parallel simulation using multiprocessing.Pool
                # Use spawn context explicitly for Windows compatibility
                games_completed = 0
                ctx = multiprocessing.get_context('spawn')
                with ctx.Pool(processes=num_workers) as pool:
                    # imap_unordered returns results as they complete
                    for result in pool.imap_unordered(simulate_game_worker, game_args, chunksize=1):
                        games_completed += 1
                        
                        if games_completed % 10 == 0 or games_completed == total_games:
                            progress_text.text(f"Completed {games_completed}/{total_games} games...")
                            progress_bar.progress(games_completed / total_games)
                        
                        # Update records
                        away_name = result.away_team_name
                        home_name = result.home_team_name
                        
                        team_records[away_name]['runs_for'] += result.away_score
                        team_records[away_name]['runs_against'] += result.home_score
                        team_records[home_name]['runs_for'] += result.home_score
                        team_records[home_name]['runs_against'] += result.away_score
                        
                        if result.away_score > result.home_score:
                            team_records[away_name]['wins'] += 1
                            team_records[home_name]['losses'] += 1
                        else:
                            team_records[home_name]['wins'] += 1
                            team_records[away_name]['losses'] += 1
                        
                        # Update series metrics using MockGameState adapter
                        mock_state = MockGameState(result)
                        series_metrics.update_from_game(mock_state)
                        
                        all_game_results.append(result)
                
                elapsed = (pd.Timestamp.now() - start_time).total_seconds()
                progress_text.text(f"Completed {total_games} games in {elapsed:.1f}s ({total_games/elapsed:.1f} games/sec)")
                
                # Calculate Standings
                standings = []
                for team_name, record in team_records.items():
                    run_diff = record['runs_for'] - record['runs_against']
                    total_decisions = record['wins'] + record['losses']
                    win_pct = record['wins'] / total_decisions if total_decisions > 0 else 0.0
                    
                    standings.append({
                        'team': team_name,
                        'wins': record['wins'],
                        'losses': record['losses'],
                        'win_pct': win_pct,
                        'run_diff': run_diff,
                        'runs_for': record['runs_for'],
                        'runs_against': record['runs_against']
                    })
                
                standings.sort(key=lambda x: (x['wins'], x['run_diff']), reverse=True)
                
                # Get series metrics data
                series_data = series_metrics.get_summary_data()
                
                st.session_state.season_results = {
                    'standings': standings,
                    'game_results': all_game_results,
                    'series_metrics': series_data
                }
                    
                st.success("Simulation Complete!")
                progress_text.empty()

        # Display Results (from Session State)
        if st.session_state.season_results:
            results = st.session_state.season_results
            standings = results['standings']
            all_game_results = results['game_results']
            series_data = results['series_metrics']
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Standings & Overview", "⚾ Comprehensive Stats", "🎯 MLB Realism"])
            
            with tab1:
                # 1. Final Standings
                st.subheader("Final Standings")
                df_standings = pd.DataFrame(standings)
                df_standings = df_standings[['team', 'wins', 'losses', 'win_pct', 'run_diff', 'runs_for', 'runs_against']]
                df_standings.columns = ['Team', 'W', 'L', 'Pct', 'Run Diff', 'RS', 'RA']
                st.dataframe(df_standings.style.format({'Pct': '{:.3f}'}))
                
                # 2. League Statistics
                st.subheader("League Statistics")
                
                # GameState objects: calculate total runs manually
                runs_per_game = [g.away_score + g.home_score for g in all_game_results]
                avg_runs = np.mean(runs_per_game)
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Avg Runs/Game", f"{avg_runs:.2f}")
                    st.metric("Total Games", len(all_game_results))
                
                with col_b:
                    fig_hist, ax_hist = plt.subplots()
                    ax_hist.hist(runs_per_game, bins=range(min(runs_per_game), max(runs_per_game) + 2), edgecolor='black', alpha=0.7)
                    ax_hist.axvline(avg_runs, color='red', linestyle='dashed', linewidth=1, label=f'Avg: {avg_runs:.1f}')
                    ax_hist.set_title("Distribution of Runs per Game")
                    ax_hist.set_xlabel("Total Runs")
                    ax_hist.set_ylabel("Frequency")
                    ax_hist.legend()
                    st.pyplot(fig_hist)
                
                # 3. Scatter Plot: Win % vs Run Differential
                st.subheader("Win % vs Run Differential")
                
                fig_scatter, ax_scatter = plt.subplots()
                teams_x = df_standings['Run Diff']
                teams_y = df_standings['Pct']
                team_labels = df_standings['Team']
                
                ax_scatter.scatter(teams_x, teams_y, color='blue')
                for i, txt in enumerate(team_labels):
                    ax_scatter.annotate(txt, (teams_x.iloc[i], teams_y.iloc[i]), xytext=(5, 5), textcoords='offset points')
                
                ax_scatter.set_xlabel("Run Differential")
                ax_scatter.set_ylabel("Win Percentage")
                ax_scatter.set_title("Pythagorean Expectation Check")
                ax_scatter.grid(True, linestyle='--', alpha=0.5)
                st.pyplot(fig_scatter)
            
            with tab2:
                display_comprehensive_stats(series_data)
            
            with tab3:
                display_realism_benchmarks(series_data)

    # --- Mode 3: Database Viewer ---
    elif mode == "Database Viewer":
        display_database_viewer()


def display_database_viewer():
    """Display comprehensive database viewer with all player attributes."""
    import sqlite3
    
    st.header("📊 Database Viewer")
    
    db_path = "baseball_teams.db"
    if not os.path.exists(db_path):
        st.error("Database not found! Please add teams first.")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Get database overview
    cursor = conn.cursor()
    
    # Count teams
    cursor.execute("SELECT COUNT(*) FROM teams")
    num_teams = cursor.fetchone()[0]
    
    # Count pitchers
    cursor.execute("SELECT COUNT(*) FROM pitchers")
    num_pitchers = cursor.fetchone()[0]
    
    # Count hitters
    cursor.execute("SELECT COUNT(*) FROM hitters")
    num_hitters = cursor.fetchone()[0]
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Teams", num_teams)
    with col2:
        st.metric("Total Pitchers", num_pitchers)
    with col3:
        st.metric("Total Hitters", num_hitters)
    
    # Tab selection for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🏟️ Teams", "⚾ Pitchers", "🏏 Hitters", "📈 Raw Tables"])
    
    with tab1:
        display_teams_tab(conn)
    
    with tab2:
        display_pitchers_tab(conn)
    
    with tab3:
        display_hitters_tab(conn)
    
    with tab4:
        display_raw_tables_tab(conn)
    
    conn.close()


def display_teams_tab(conn):
    """Display teams overview."""
    st.subheader("Teams in Database")
    
    teams_df = pd.read_sql_query("""
        SELECT 
            t.team_name as "Team Name",
            t.team_abbr as "Abbr",
            t.season as "Season",
            t.league as "League",
            t.division as "Division",
            (SELECT COUNT(*) FROM team_rosters tr 
             JOIN pitchers p ON tr.pitcher_id = p.pitcher_id 
             WHERE tr.team_id = t.team_id) as "Pitchers",
            (SELECT COUNT(*) FROM team_rosters tr 
             JOIN hitters h ON tr.hitter_id = h.hitter_id 
             WHERE tr.team_id = t.team_id) as "Hitters"
        FROM teams t
        ORDER BY t.season DESC, t.team_name
    """, conn)
    
    if len(teams_df) > 0:
        st.dataframe(teams_df, hide_index=True, use_container_width=True)
        
        # Team selector for roster view
        st.subheader("Team Roster")
        team_options = teams_df.apply(lambda x: f"{x['Team Name']} ({x['Season']})", axis=1).tolist()
        selected_team = st.selectbox("Select Team to View Roster", team_options)
        
        if selected_team:
            team_name = selected_team.rsplit(" (", 1)[0]
            season = int(selected_team.rsplit(" (", 1)[1].rstrip(")"))
            
            # Get team_id
            cursor = conn.cursor()
            cursor.execute("SELECT team_id FROM teams WHERE team_name = ? AND season = ?", (team_name, season))
            result = cursor.fetchone()
            
            if result:
                team_id = result[0]
                
                # Get pitchers for this team
                pitchers_df = pd.read_sql_query(f"""
                    SELECT 
                        p.player_name as "Name",
                        p.hand as "Hand",
                        CASE WHEN tr.is_starter = 1 THEN 'SP' ELSE 'RP' END as "Role",
                        p.velocity as "Velocity",
                        p.command as "Command",
                        p.stamina as "Stamina",
                        p.movement as "Movement",
                        p.putaway_skill as "Putaway",
                        ROUND(p.era, 2) as "ERA",
                        ROUND(p.whip, 2) as "WHIP",
                        ROUND(p.k_per_9, 1) as "K/9",
                        ROUND(p.bb_per_9, 1) as "BB/9",
                        ROUND(p.innings_pitched, 1) as "IP"
                    FROM pitchers p
                    JOIN team_rosters tr ON p.pitcher_id = tr.pitcher_id
                    WHERE tr.team_id = {team_id}
                    ORDER BY tr.is_starter DESC, p.innings_pitched DESC
                """, conn)
                
                # Get hitters for this team
                hitters_df = pd.read_sql_query(f"""
                    SELECT 
                        h.player_name as "Name",
                        tr.batting_order as "Order",
                        h.primary_position as "Pos",
                        h.hand as "Hand",
                        h.contact as "Contact",
                        h.power as "Power",
                        h.discipline as "Discipline",
                        h.speed as "Speed",
                        h.vision as "Vision",
                        ROUND(h.batting_avg, 3) as "AVG",
                        ROUND(h.on_base_pct, 3) as "OBP",
                        ROUND(h.slugging_pct, 3) as "SLG",
                        h.home_runs as "HR",
                        ROUND(h.avg_exit_velo, 1) as "Exit Velo"
                    FROM hitters h
                    JOIN team_rosters tr ON h.hitter_id = tr.hitter_id
                    WHERE tr.team_id = {team_id}
                    ORDER BY tr.batting_order
                """, conn)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Pitching Staff**")
                    if len(pitchers_df) > 0:
                        st.dataframe(pitchers_df, hide_index=True, use_container_width=True)
                    else:
                        st.info("No pitchers found")
                
                with col2:
                    st.markdown("**Lineup**")
                    if len(hitters_df) > 0:
                        st.dataframe(hitters_df, hide_index=True, use_container_width=True)
                    else:
                        st.info("No hitters found")
    else:
        st.info("No teams in database")


def display_pitchers_tab(conn):
    """Display all pitchers with full attributes."""
    st.subheader("All Pitchers")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        min_ip = st.slider("Minimum Innings Pitched", 0, 200, 0)
    with col2:
        sort_by = st.selectbox("Sort By", ["Name", "Velocity", "Command", "ERA", "K/9", "WHIP"])
    
    sort_map = {
        "Name": "player_name",
        "Velocity": "velocity DESC",
        "Command": "command DESC", 
        "ERA": "era",
        "K/9": "k_per_9 DESC",
        "WHIP": "whip"
    }
    
    pitchers_df = pd.read_sql_query(f"""
        SELECT 
            p.player_name as "Name",
            t.team_abbr as "Team",
            p.season as "Year",
            p.hand as "Hand",
            
            -- Game Attributes (0-100k scale)
            p.velocity as "VELOCITY",
            p.command as "COMMAND",
            p.stamina as "STAMINA",
            p.movement as "MOVEMENT",
            p.repertoire as "REPERTOIRE",
            p.putaway_skill as "PUTAWAY",
            ROUND(p.nibbling_tendency, 3) as "NIBBLE",
            
            -- MLB Stats
            ROUND(p.era, 2) as "ERA",
            ROUND(p.whip, 2) as "WHIP",
            p.strikeouts as "K",
            p.walks as "BB",
            ROUND(p.k_per_9, 1) as "K/9",
            ROUND(p.bb_per_9, 1) as "BB/9",
            ROUND(p.innings_pitched, 1) as "IP",
            ROUND(p.avg_fastball_velo, 1) as "FB Velo",
            p.games_pitched as "G"
        FROM pitchers p
        LEFT JOIN team_rosters tr ON p.pitcher_id = tr.pitcher_id
        LEFT JOIN teams t ON tr.team_id = t.team_id
        WHERE (p.innings_pitched >= {min_ip} OR p.innings_pitched IS NULL)
        ORDER BY {sort_map[sort_by]}
    """, conn)
    
    if len(pitchers_df) > 0:
        st.markdown(f"**{len(pitchers_df)} pitchers**")
        st.dataframe(pitchers_df, hide_index=True, use_container_width=True, height=500)
        
        # Attribute distribution
        st.subheader("Attribute Distributions")
        
        attr_cols = ["VELOCITY", "COMMAND", "STAMINA", "MOVEMENT", "PUTAWAY"]
        available_attrs = [c for c in attr_cols if c in pitchers_df.columns and pitchers_df[c].notna().any()]
        
        if available_attrs:
            selected_attr = st.selectbox("Select Attribute", available_attrs)
            
            fig, ax = plt.subplots(figsize=(10, 4))
            data = pitchers_df[selected_attr].dropna()
            ax.hist(data, bins=30, edgecolor='black', alpha=0.7)
            ax.axvline(data.mean(), color='red', linestyle='dashed', label=f'Mean: {data.mean():.0f}')
            ax.axvline(50000, color='green', linestyle='dashed', label='League Avg (50k)')
            ax.axvline(85000, color='orange', linestyle='dashed', label='Elite (85k)')
            ax.set_xlabel(selected_attr)
            ax.set_ylabel("Count")
            ax.set_title(f"Distribution of {selected_attr}")
            ax.legend()
            st.pyplot(fig)
    else:
        st.info("No pitchers found matching criteria")


def display_hitters_tab(conn):
    """Display all hitters with full attributes."""
    st.subheader("All Hitters")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        min_ab = st.slider("Minimum At-Bats", 0, 600, 0)
    with col2:
        position_filter = st.selectbox("Position", ["All", "C", "1B", "2B", "SS", "3B", "LF", "CF", "RF", "DH"])
    with col3:
        sort_by = st.selectbox("Sort By", ["Name", "Contact", "Power", "Speed", "OPS", "Exit Velo"])
    
    sort_map = {
        "Name": "player_name",
        "Contact": "contact DESC",
        "Power": "power DESC",
        "Speed": "speed DESC",
        "OPS": "ops DESC",
        "Exit Velo": "avg_exit_velo DESC"
    }
    
    pos_filter = "" if position_filter == "All" else f"AND h.primary_position = '{position_filter}'"
    
    hitters_df = pd.read_sql_query(f"""
        SELECT 
            h.player_name as "Name",
            t.team_abbr as "Team",
            h.season as "Year",
            h.primary_position as "Pos",
            h.hand as "Hand",
            
            -- Game Attributes Offensive (0-100k scale)
            h.contact as "CONTACT",
            h.power as "POWER",
            h.discipline as "DISCIPLINE",
            h.speed as "SPEED",
            h.vision as "VISION",
            h.attack_angle_control as "ATTACK_ANGLE",
            
            -- Game Attributes Defensive (0-100k scale)
            h.reaction_time as "REACTION",
            h.top_sprint_speed as "SPRINT",
            h.route_efficiency as "ROUTE",
            h.arm_strength as "ARM_STR",
            h.arm_accuracy as "ARM_ACC",
            h.fielding_secure as "FIELDING",
            h.jump_attr as "JUMP",
            h.burst_attr as "BURST",
            
            -- MLB Stats
            ROUND(h.batting_avg, 3) as "AVG",
            ROUND(h.on_base_pct, 3) as "OBP",
            ROUND(h.slugging_pct, 3) as "SLG",
            ROUND(h.ops, 3) as "OPS",
            h.home_runs as "HR",
            h.stolen_bases as "SB",
            h.strikeouts as "K",
            h.walks as "BB",
            ROUND(h.avg_exit_velo, 1) as "EV",
            ROUND(h.max_exit_velo, 1) as "MaxEV",
            ROUND(h.barrel_pct, 1) as "Barrel%",
            ROUND(h.sprint_speed, 1) as "SprintSpd",
            h.at_bats as "AB",
            h.games_played as "G"
        FROM hitters h
        LEFT JOIN team_rosters tr ON h.hitter_id = tr.hitter_id
        LEFT JOIN teams t ON tr.team_id = t.team_id
        WHERE (h.at_bats >= {min_ab} OR h.at_bats IS NULL)
        {pos_filter}
        ORDER BY {sort_map[sort_by]}
    """, conn)
    
    if len(hitters_df) > 0:
        st.markdown(f"**{len(hitters_df)} hitters**")
        st.dataframe(hitters_df, hide_index=True, use_container_width=True, height=500)
        
        # Attribute distribution
        st.subheader("Attribute Distributions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Offensive Attributes**")
            off_attrs = ["CONTACT", "POWER", "DISCIPLINE", "SPEED", "VISION"]
            available_off = [c for c in off_attrs if c in hitters_df.columns and hitters_df[c].notna().any()]
            
            if available_off:
                selected_off = st.selectbox("Select Offensive Attribute", available_off, key="off_attr")
                
                fig, ax = plt.subplots(figsize=(8, 4))
                data = hitters_df[selected_off].dropna()
                ax.hist(data, bins=30, edgecolor='black', alpha=0.7, color='blue')
                ax.axvline(data.mean(), color='red', linestyle='dashed', label=f'Mean: {data.mean():.0f}')
                ax.axvline(50000, color='green', linestyle='dashed', label='League Avg (50k)')
                ax.axvline(85000, color='orange', linestyle='dashed', label='Elite (85k)')
                ax.set_xlabel(selected_off)
                ax.set_ylabel("Count")
                ax.legend()
                st.pyplot(fig)
        
        with col2:
            st.markdown("**Defensive Attributes**")
            def_attrs = ["REACTION", "SPRINT", "ROUTE", "ARM_STR", "FIELDING", "JUMP", "BURST"]
            available_def = [c for c in def_attrs if c in hitters_df.columns and hitters_df[c].notna().any()]
            
            if available_def:
                selected_def = st.selectbox("Select Defensive Attribute", available_def, key="def_attr")
                
                fig, ax = plt.subplots(figsize=(8, 4))
                data = hitters_df[selected_def].dropna()
                ax.hist(data, bins=30, edgecolor='black', alpha=0.7, color='green')
                ax.axvline(data.mean(), color='red', linestyle='dashed', label=f'Mean: {data.mean():.0f}')
                ax.axvline(50000, color='blue', linestyle='dashed', label='League Avg (50k)')
                ax.axvline(85000, color='orange', linestyle='dashed', label='Elite (85k)')
                ax.set_xlabel(selected_def)
                ax.set_ylabel("Count")
                ax.legend()
                st.pyplot(fig)
        
        # Scatter plot for relationships
        st.subheader("Attribute Relationships")
        col1, col2 = st.columns(2)
        
        with col1:
            x_attr = st.selectbox("X-Axis", ["POWER", "CONTACT", "SPEED", "DISCIPLINE"], key="x_scatter")
        with col2:
            y_attr = st.selectbox("Y-Axis", ["OPS", "AVG", "SLG", "HR"], key="y_scatter")
        
        if x_attr in hitters_df.columns and y_attr in hitters_df.columns:
            plot_df = hitters_df[[x_attr, y_attr, "Name"]].dropna()
            
            if len(plot_df) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.scatter(plot_df[x_attr], plot_df[y_attr], alpha=0.6)
                ax.set_xlabel(x_attr)
                ax.set_ylabel(y_attr)
                ax.set_title(f"{x_attr} vs {y_attr}")
                
                # Add trend line
                z = np.polyfit(plot_df[x_attr], plot_df[y_attr], 1)
                p = np.poly1d(z)
                ax.plot(sorted(plot_df[x_attr]), p(sorted(plot_df[x_attr])), "r--", alpha=0.8, label="Trend")
                ax.legend()
                st.pyplot(fig)
    else:
        st.info("No hitters found matching criteria")


def display_raw_tables_tab(conn):
    """Display raw database tables for debugging."""
    st.subheader("Raw Database Tables")
    
    st.warning("⚠️ This view shows raw database contents for debugging purposes.")
    
    table_choice = st.selectbox("Select Table", ["teams", "pitchers", "hitters", "team_rosters"])
    
    # Get column info
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_choice})")
    columns = cursor.fetchall()
    
    st.markdown(f"**Table Schema: {table_choice}**")
    schema_df = pd.DataFrame(columns, columns=["ID", "Name", "Type", "NotNull", "Default", "PK"])
    st.dataframe(schema_df[["Name", "Type", "NotNull", "PK"]], hide_index=True)
    
    # Show data with limit
    limit = st.number_input("Row Limit", min_value=10, max_value=1000, value=100)
    
    df = pd.read_sql_query(f"SELECT * FROM {table_choice} LIMIT {limit}", conn)
    st.markdown(f"**Data ({len(df)} rows shown)**")
    st.dataframe(df, hide_index=True, use_container_width=True, height=400)
    
    # Export option
    if st.button("Download as CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{table_choice}_export.csv",
            mime="text/csv"
        )


def display_comprehensive_stats(series_data: dict):
    """Display comprehensive series statistics in Streamlit."""
    
    overview = series_data['overview']
    run_prod = series_data['run_production']
    
    # Series Overview
    st.subheader("📊 Series Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Games Played", overview['games_played'])
    with col2:
        st.metric(f"{overview['away_team']}", f"{overview['away_wins']}-{overview['home_wins']}")
    with col3:
        st.metric(f"{overview['home_team']}", f"{overview['home_wins']}-{overview['away_wins']}")
    
    # Run Production
    st.subheader("🏃 Run Production")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{overview['away_team']}**")
        st.write(f"Total: {run_prod['away']['total']} ({run_prod['away']['per_game']:.2f} per game)")
        st.write(f"Range: {run_prod['away']['min']}-{run_prod['away']['max']} runs")
        st.write(f"Std Dev: {run_prod['away']['std_dev']:.2f}")
    
    with col2:
        st.markdown(f"**{overview['home_team']}**")
        st.write(f"Total: {run_prod['home']['total']} ({run_prod['home']['per_game']:.2f} per game)")
        st.write(f"Range: {run_prod['home']['min']}-{run_prod['home']['max']} runs")
        st.write(f"Std Dev: {run_prod['home']['std_dev']:.2f}")
    
    # Batting Statistics
    st.subheader("⚾ Batting Statistics")
    
    for side, label in [('away', overview['away_team']), ('home', overview['home_team'])]:
        batting = series_data['batting'][side]
        
        with st.expander(f"**{label}**", expanded=True):
            # Triple Slash and Advanced
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg = batting['triple_slash']['avg']
                obp = batting['triple_slash']['obp']
                slg = batting['triple_slash']['slg']
                st.metric("Triple Slash", f".{int(avg*1000):03d}/.{int(obp*1000):03d}/.{int(slg*1000):03d}")
            with col2:
                st.metric("OPS", f"{batting['ops']:.3f}")
            with col3:
                st.metric("wOBA", f"{batting['woba']:.3f}", help="MLB avg ~0.320")
            with col4:
                st.metric("ISO", f"{batting['power']['iso']:.3f}", help="MLB avg ~0.150")
            
            # Plate Discipline
            st.markdown("**Plate Discipline**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("K Rate", f"{batting['plate_discipline']['k_rate']*100:.1f}%", help="MLB avg ~22%")
            with col2:
                st.metric("BB Rate", f"{batting['plate_discipline']['bb_rate']*100:.1f}%", help="MLB avg ~8.5%")
            with col3:
                st.metric("K/BB Ratio", f"{batting['plate_discipline']['k_bb_ratio']:.2f}")
            
            # Power Metrics
            st.markdown("**Power Metrics**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("HR/FB", f"{batting['power']['hr_fb']*100:.1f}%", help="MLB avg ~12.5%")
            with col2:
                st.metric("Home Runs", batting['power']['home_runs'])
            with col3:
                st.metric("HR/Game", f"{batting['power']['hr_per_game']:.1f}")
            
            # Contact Quality
            st.markdown("**Contact Quality**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("BABIP", f"{batting['contact_quality']['babip']:.3f}", help="MLB range: .260-.360")
            with col2:
                st.metric("Avg Exit Velo", f"{batting['contact_quality']['avg_exit_velo']:.1f} mph", help="MLB avg ~88 mph")
            with col3:
                st.metric("Hard Hit Rate", f"{batting['contact_quality']['hard_hit_rate']*100:.1f}%", help="MLB avg ~40%")
            with col4:
                st.metric("Barrel Rate", f"{batting['contact_quality']['barrel_rate']*100:.1f}%", help="MLB avg ~8%")
            
            # Batted Ball Distribution
            st.markdown("**Batted Ball Distribution**")
            bb_dist = batting['batted_ball_distribution']
            dist_data = pd.DataFrame({
                'Type': ['Ground Balls', 'Line Drives', 'Fly Balls'],
                'Percentage': [bb_dist['ground_balls']*100, bb_dist['line_drives']*100, bb_dist['fly_balls']*100],
                'MLB Avg': [45.0, 21.0, 34.0]
            })
            st.dataframe(dist_data.style.format({'Percentage': '{:.1f}%', 'MLB Avg': '{:.1f}%'}), hide_index=True)
    
    # Pitching Statistics
    st.subheader("🎯 Pitching Statistics")
    
    for side, label in [('away', overview['away_team']), ('home', overview['home_team'])]:
        pitching = series_data['pitching'][side]
        
        with st.expander(f"**{label}**", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ERA", f"{pitching['era']:.2f}", help="MLB avg ~4.25")
                st.metric("WHIP", f"{pitching['whip']:.2f}", help="MLB avg ~1.30")
            with col2:
                st.metric("K/9", f"{pitching['k_per_9']:.1f}", help="MLB avg ~8.5")
                st.metric("BB/9", f"{pitching['bb_per_9']:.1f}", help="MLB avg ~3.0")
            with col3:
                st.metric("HR/9", f"{pitching['hr_per_9']:.2f}", help="MLB avg ~1.2")
                st.metric("K/BB Ratio", f"{pitching['k_bb_ratio']:.2f}", help="MLB avg ~2.8")
            
            st.markdown("**Totals**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"IP: {pitching['totals']['innings_pitched']:.1f}")
            with col2:
                st.write(f"Batters Faced: {pitching['totals']['batters_faced']}")
            with col3:
                st.write(f"Pitches: {pitching['totals']['pitches_thrown']}")
    
    # Fielding Statistics
    st.subheader("🧤 Fielding Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        fielding_away = series_data['fielding']['away']
        st.markdown(f"**{overview['away_team']}**")
        st.write(f"Errors: {fielding_away['errors']} ({fielding_away['errors_per_game']:.1f} per game)")
    
    with col2:
        fielding_home = series_data['fielding']['home']
        st.markdown(f"**{overview['home_team']}**")
        st.write(f"Errors: {fielding_home['errors']} ({fielding_home['errors_per_game']:.1f} per game)")


def display_realism_benchmarks(series_data: dict):
    """Display MLB realism benchmarks in Streamlit."""
    
    realism = series_data['realism_checks']
    summary = realism['summary']
    checks = realism['checks']
    
    st.subheader("🎯 MLB Realism Benchmarks")
    
    if not checks:
        st.warning("⚠️ Not enough data for realism checks (need 20+ at-bats)")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Metrics", summary['total'])
    with col2:
        st.metric("✓ Within Range", summary['ok'], delta=None)
    with col3:
        st.metric("⚠️ Warnings", summary['warning'], delta=None, delta_color="off")
    with col4:
        st.metric("🚨 Critical", summary['critical'], delta=None, delta_color="off")
    
    # Progress indicator
    pass_rate = summary['ok'] / summary['total'] if summary['total'] > 0 else 0
    st.progress(pass_rate, text=f"{summary['ok']}/{summary['total']} metrics within MLB range ({pass_rate*100:.0f}%)")
    
    # Detailed checks table
    st.subheader("Detailed Metrics")
    
    check_data = []
    for check in checks:
        mlb_range = f"{check['mlb_min']:.3f} - {check['mlb_max']:.3f}"
        if check['mlb_avg'] is not None:
            mlb_range += f" (avg {check['mlb_avg']:.3f})"
        
        check_data.append({
            'Status': check['emoji'],
            'Metric': check['metric_name'],
            'Actual': f"{check['actual_value']:.3f}",
            'MLB Range': mlb_range,
        })
    
    df_checks = pd.DataFrame(check_data)
    st.dataframe(df_checks, hide_index=True, use_container_width=True)
    
    # Warnings section
    warning_checks = [c for c in checks if c['status'] == 'WARNING']
    if warning_checks:
        st.subheader("⚠️ Warnings")
        for check in warning_checks:
            st.warning(f"**{check['metric_name']}**: {check['actual_value']:.3f} (outside range {check['mlb_min']:.3f}-{check['mlb_max']:.3f})")
    
    # Critical issues section
    critical_checks = [c for c in checks if c['status'] == 'CRITICAL']
    if critical_checks:
        st.subheader("🚨 Critical Issues")
        for check in critical_checks:
            st.error(f"**{check['metric_name']}**: {check['actual_value']:.3f} (far from MLB avg {check['mlb_avg']:.3f})")
    
    # Success message
    if not warning_checks and not critical_checks:
        st.success("✅ All metrics within expected MLB ranges!")


if __name__ == "__main__":
    main()

