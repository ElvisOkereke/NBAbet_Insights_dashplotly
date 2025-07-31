import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import threading
import time
import uvicorn
from src.api.main import app as fastapi_app
from src.data.data_service import DataService

# Initialize data service
data_service = DataService()
data_service.seed_sample_data()

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
app.title = "NBA Betting Research MVP"

# Start FastAPI server in background thread
def start_fastapi():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")

api_thread = threading.Thread(target=start_fastapi, daemon=True)
api_thread.start()

# Wait a moment for API to start
time.sleep(2)

# API base URL
API_BASE = "http://127.0.0.1:8000/api"

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🏀 NBA Betting Research MVP", className="text-center mb-4"),
            html.P("Analyze NBA player performance and betting insights", className="lead text-center mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Recent Games", className="card-title"),
                    html.Div(id="recent-games-table")
                ])
            ])
        ], width=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Teams Overview", className="card-title"),
                    html.Div(id="teams-table")
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Player Analysis", className="card-title"),
                    dcc.Dropdown(
                        id="player-dropdown",
                        placeholder="Select a player to analyze",
                        className="mb-3"
                    ),
                    html.Div(id="player-stats-content")
                ])
            ])
        ], width=8),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Betting Insights", className="card-title"),
                    html.Div(id="betting-insights-content")
                ])
            ])
        ], width=4)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Player Performance Chart", className="card-title"),
                    dcc.Graph(id="player-performance-chart")
                ])
            ])
        ])
    ])
], fluid=True)

@callback(
    Output("recent-games-table", "children"),
    Input("recent-games-table", "id")
)
def update_recent_games(_):
    try:
        response = requests.get(f"{API_BASE}/games/recent?limit=5")
        if response.status_code == 200:
            games = response.json()["games"]
            
            df = pd.DataFrame(games)
            if not df.empty:
                df["matchup"] = df["away_team"] + " @ " + df["home_team"]
                df["score"] = df["away_score"].astype(str) + " - " + df["home_score"].astype(str)
                
                return dash_table.DataTable(
                    data=df[["date", "matchup", "score", "status"]].to_dict("records"),
                    columns=[
                        {"name": "Date", "id": "date"},
                        {"name": "Matchup", "id": "matchup"},
                        {"name": "Score", "id": "score"},
                        {"name": "Status", "id": "status"}
                    ],
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{status} = completed'},
                            'backgroundColor': '#d4edda'
                        }
                    ]
                )
        
        return html.P("No recent games data available", className="text-muted")
    except Exception as e:
        return html.P(f"Error loading games: {str(e)}", className="text-danger")

@callback(
    Output("teams-table", "children"),
    Input("teams-table", "id")
)
def update_teams(_):
    try:
        response = requests.get(f"{API_BASE}/teams")
        if response.status_code == 200:
            teams = response.json()["teams"]
            
            df = pd.DataFrame(teams)
            if not df.empty:
                df["record"] = df["wins"].astype(str) + "-" + df["losses"].astype(str)
                df["win_pct"] = (df["wins"] / (df["wins"] + df["losses"]) * 100).round(1)
                
                return dash_table.DataTable(
                    data=df[["name", "city", "record", "win_pct"]].to_dict("records"),
                    columns=[
                        {"name": "Team", "id": "name"},
                        {"name": "City", "id": "city"},
                        {"name": "Record", "id": "record"},
                        {"name": "Win %", "id": "win_pct", "type": "numeric", "format": {"specifier": ".1f"}}
                    ],
                    style_cell={'textAlign': 'left'},
                    sort_action="native"
                )
        
        return html.P("No teams data available", className="text-muted")
    except Exception as e:
        return html.P(f"Error loading teams: {str(e)}", className="text-danger")

@callback(
    Output("player-dropdown", "options"),
    Input("player-dropdown", "id")
)
def update_player_dropdown(_):
    try:
        response = requests.get(f"{API_BASE}/players")
        if response.status_code == 200:
            players = response.json()["players"]
            return [{"label": player["name"], "value": player["id"]} for player in players]
        return []
    except:
        return []

@callback(
    [Output("player-stats-content", "children"),
     Output("betting-insights-content", "children"),
     Output("player-performance-chart", "figure")],
    Input("player-dropdown", "value")
)
def update_player_analysis(player_id):
    if not player_id:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Select a player to view analysis", 
                               xref="paper", yref="paper", 
                               x=0.5, y=0.5, showarrow=False)
        return html.P("Select a player to view stats"), html.P("Select a player for insights"), empty_fig
    
    try:
        # Get player stats
        stats_response = requests.get(f"{API_BASE}/players/{player_id}/stats")
        insights_response = requests.get(f"{API_BASE}/players/{player_id}/insights")
        
        stats_content = html.P("No stats available")
        insights_content = html.P("No insights available")
        chart_fig = go.Figure()
        
        if stats_response.status_code == 200:
            stats = stats_response.json()["stats"]
            
            if stats.get("games_played", 0) > 0:
                stats_content = dbc.Row([
                    dbc.Col([
                        html.H6(f"{stats['name']} ({stats['team']})", className="mb-2"),
                        html.P(f"Position: {stats['position']}", className="mb-1"),
                        html.P(f"Games Played: {stats['games_played']}", className="mb-1"),
                    ], width=6),
                    dbc.Col([
                        html.P(f"PPG: {stats['avg_points']}", className="mb-1"),
                        html.P(f"APG: {stats['avg_assists']}", className="mb-1"),
                        html.P(f"RPG: {stats['avg_rebounds']}", className="mb-1"),
                        html.P(f"FG%: {stats['fg_percentage']}%", className="mb-1"),
                        html.P(f"3P%: {stats['three_pt_percentage']}%", className="mb-1")
                    ], width=6)
                ])
                
                # Create performance chart
                categories = ['Points', 'Assists', 'Rebounds', 'FG%', '3P%']
                values = [
                    stats['avg_points'],
                    stats['avg_assists'],
                    stats['avg_rebounds'],
                    stats['fg_percentage'],
                    stats['three_pt_percentage']
                ]
                
                chart_fig = go.Figure()
                chart_fig.add_trace(go.Bar(
                    x=categories,
                    y=values,
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
                ))
                chart_fig.update_layout(
                    title=f"{stats['name']} - Season Averages",
                    xaxis_title="Statistics",
                    yaxis_title="Value",
                    height=400
                )
        
        if insights_response.status_code == 200:
            insights = insights_response.json()["insights"]
            
            if "insights" in insights and insights["insights"]:
                insight_items = [html.Li(insight) for insight in insights["insights"]]
                recommendation_color = "success" if insights.get("recommendation") == "BUY" else "warning"
                
                insights_content = html.Div([
                    html.H6(f"Analysis for {insights.get('player', 'Player')}", className="mb-3"),
                    html.Ul(insight_items, className="mb-3"),
                    dbc.Badge(
                        f"Recommendation: {insights.get('recommendation', 'HOLD')}", 
                        color=recommendation_color, 
                        className="mb-2"
                    )
                ])
        
        return stats_content, insights_content, chart_fig
        
    except Exception as e:
        error_msg = html.P(f"Error: {str(e)}", className="text-danger")
        empty_fig = go.Figure()
        return error_msg, error_msg, empty_fig

if __name__ == "__main__":
    app.run(debug=True, port=8050, host="127.0.0.1")
