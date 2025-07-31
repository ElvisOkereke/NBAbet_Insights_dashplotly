import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import random

from ..models.database import (
    Team, Player, Game, PlayerPerformance, Odds,
    SessionLocal, create_tables
)

class DataService:
    def __init__(self):
        create_tables()
        self.db = SessionLocal()
    
    def seed_sample_data(self):
        """Seed the database with sample NBA data for testing"""
        # Check if data already exists
        if self.db.query(Team).count() > 0:
            return
        
        # Sample NBA teams
        teams_data = [
            {"name": "Lakers", "city": "Los Angeles", "conference": "Western", "division": "Pacific"},
            {"name": "Warriors", "city": "Golden State", "conference": "Western", "division": "Pacific"},
            {"name": "Celtics", "city": "Boston", "conference": "Eastern", "division": "Atlantic"},
            {"name": "Heat", "city": "Miami", "conference": "Eastern", "division": "Southeast"},
            {"name": "Nuggets", "city": "Denver", "conference": "Western", "division": "Northwest"},
            {"name": "76ers", "city": "Philadelphia", "conference": "Eastern", "division": "Atlantic"},
        ]
        
        teams = []
        for team_data in teams_data:
            team = Team(**team_data, wins=random.randint(30, 60), losses=random.randint(22, 52))
            self.db.add(team)
            teams.append(team)
        
        self.db.commit()
        
        # Sample players
        player_names = [
            "LeBron James", "Stephen Curry", "Jayson Tatum", "Jimmy Butler",
            "Nikola Jokic", "Joel Embiid", "Anthony Davis", "Klay Thompson",
            "Jaylen Brown", "Tyler Herro", "Jamal Murray", "James Harden"
        ]
        
        positions = ["PG", "SG", "SF", "PF", "C"]
        
        for i, name in enumerate(player_names):
            player = Player(
                name=name,
                team_id=teams[i % len(teams)].id,
                position=random.choice(positions),
                age=random.randint(22, 38),
                height=f"{random.randint(6, 7)}'{random.randint(0, 11)}\"",
                weight=random.randint(180, 280),
                injury_status=random.choice(["healthy", "probable", "questionable"])
            )
            self.db.add(player)
        
        self.db.commit()
        
        # Sample games and performances
        players = self.db.query(Player).all()
        
        for i in range(20):  # Create 20 sample games
            home_team = random.choice(teams)
            away_team = random.choice([t for t in teams if t.id != home_team.id])
            
            game_date = datetime.now() - timedelta(days=random.randint(1, 30))
            home_score = random.randint(90, 130)
            away_score = random.randint(90, 130)
            
            game = Game(
                date=game_date,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                home_score=home_score,
                away_score=away_score,
                status="completed"
            )
            self.db.add(game)
            self.db.commit()
            
            # Add player performances for this game
            game_players = [p for p in players if p.team_id in [home_team.id, away_team.id]]
            
            for player in game_players[:10]:  # Limit to 10 players per game
                performance = PlayerPerformance(
                    player_id=player.id,
                    game_id=game.id,
                    points=random.randint(5, 35),
                    assists=random.randint(0, 12),
                    rebounds=random.randint(2, 15),
                    steals=random.randint(0, 4),
                    blocks=random.randint(0, 3),
                    turnovers=random.randint(0, 6),
                    field_goals_made=random.randint(3, 15),
                    field_goals_attempted=random.randint(8, 25),
                    three_pointers_made=random.randint(0, 8),
                    three_pointers_attempted=random.randint(0, 12),
                    free_throws_made=random.randint(0, 10),
                    free_throws_attempted=random.randint(0, 12),
                    minutes_played=random.uniform(15.0, 42.0)
                )
                self.db.add(performance)
            
            # Add odds for this game
            bookmakers = ["DraftKings", "Bet365", "FanDuel", "BetMGM"]
            bet_types = ["moneyline", "spread", "over_under"]
            
            for bookmaker in bookmakers:
                for bet_type in bet_types:
                    if bet_type == "moneyline":
                        odds_value = random.uniform(-200, 200)
                        line = None
                    elif bet_type == "spread":
                        odds_value = random.uniform(-115, -105)
                        line = random.uniform(-10, 10)
                    else:  # over_under
                        odds_value = random.uniform(-115, -105)
                        line = random.uniform(200, 240)
                    
                    odds = Odds(
                        game_id=game.id,
                        bookmaker=bookmaker,
                        bet_type=bet_type,
                        odds_value=odds_value,
                        line=line,
                        timestamp=game_date - timedelta(hours=2)
                    )
                    self.db.add(odds)
        
        self.db.commit()
    
    def get_teams(self) -> List[Dict]:
        """Get all teams"""
        teams = self.db.query(Team).all()
        return [{"id": t.id, "name": t.name, "city": t.city, "wins": t.wins, "losses": t.losses} for t in teams]
    
    def get_players(self, team_id: Optional[int] = None) -> List[Dict]:
        """Get players, optionally filtered by team"""
        query = self.db.query(Player)
        if team_id:
            query = query.filter(Player.team_id == team_id)
        
        players = query.all()
        return [{
            "id": p.id,
            "name": p.name,
            "team_id": p.team_id,
            "position": p.position,
            "age": p.age,
            "injury_status": p.injury_status
        } for p in players]
    
    def get_recent_games(self, limit: int = 10) -> List[Dict]:
        """Get recent games"""
        games = self.db.query(Game).order_by(Game.date.desc()).limit(limit).all()
        
        result = []
        for game in games:
            result.append({
                "id": game.id,
                "date": game.date.strftime("%Y-%m-%d"),
                "home_team": game.home_team.name,
                "away_team": game.away_team.name,
                "home_score": game.home_score,
                "away_score": game.away_score,
                "status": game.status
            })
        
        return result
    
    def get_player_stats(self, player_id: int) -> Dict:
        """Get player statistics"""
        player = self.db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {}
        
        performances = self.db.query(PlayerPerformance).filter(
            PlayerPerformance.player_id == player_id
        ).all()
        
        if not performances:
            return {"name": player.name, "games_played": 0}
        
        # Calculate averages
        stats = {
            "name": player.name,
            "team": player.team.name,
            "position": player.position,
            "games_played": len(performances),
            "avg_points": round(np.mean([p.points for p in performances]), 1),
            "avg_assists": round(np.mean([p.assists for p in performances]), 1),
            "avg_rebounds": round(np.mean([p.rebounds for p in performances]), 1),
            "fg_percentage": round(
                sum(p.field_goals_made for p in performances) / 
                max(sum(p.field_goals_attempted for p in performances), 1) * 100, 1
            ),
            "three_pt_percentage": round(
                sum(p.three_pointers_made for p in performances) / 
                max(sum(p.three_pointers_attempted for p in performances), 1) * 100, 1
            )
        }
        
        return stats
    
    def get_odds_comparison(self, game_id: int) -> List[Dict]:
        """Get odds comparison for a specific game"""
        odds = self.db.query(Odds).filter(Odds.game_id == game_id).all()
        
        result = []
        for odd in odds:
            result.append({
                "bookmaker": odd.bookmaker,
                "bet_type": odd.bet_type,
                "odds_value": odd.odds_value,
                "line": odd.line
            })
        
        return result
    
    def get_betting_insights(self, player_id: int) -> Dict:
        """Generate simple betting insights for a player"""
        stats = self.get_player_stats(player_id)
        
        if not stats or stats.get("games_played", 0) == 0:
            return {"insight": "Insufficient data for analysis"}
        
        insights = []
        
        # Points analysis
        avg_points = stats["avg_points"]
        if avg_points > 25:
            insights.append(f"High scorer averaging {avg_points} PPG - good for over bets")
        elif avg_points < 15:
            insights.append(f"Low scorer averaging {avg_points} PPG - consider under bets")
        
        # Shooting efficiency
        fg_pct = stats["fg_percentage"]
        if fg_pct > 50:
            insights.append(f"Excellent shooter at {fg_pct}% FG - reliable for prop bets")
        elif fg_pct < 40:
            insights.append(f"Inconsistent shooter at {fg_pct}% FG - proceed with caution")
        
        # All-around performance
        if stats["avg_assists"] > 7 and stats["avg_rebounds"] > 7:
            insights.append("Triple-double threat - good for player prop combinations")
        
        return {
            "player": stats["name"],
            "insights": insights,
            "recommendation": "BUY" if len(insights) > 1 and avg_points > 20 else "HOLD"
        }
    
    def close(self):
        self.db.close()
